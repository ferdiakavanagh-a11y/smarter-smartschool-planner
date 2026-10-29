import json
import os
from datetime import date
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QCoreApplication

import credential_store as store
import secure_session
import setup_ui
import task_state
from qml_app.backend import Backend


class SecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_vault_origin_cannot_be_changed_in_yaml(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'credentials.yml'
            target = store._prefix(path) + 'test'
            path.write_text('main_url: evil.example\nvault_target: ' + target)
            secrets = dict(username='student', password='fake', mfa='', gemini_api_key='', main_url='school.example')
            with patch.object(store, '_read', return_value=secrets):
                with self.assertRaises(store.CredentialError):
                    store.load_credentials(path)
                recovery = store.load_for_setup(path)
                self.assertEqual(recovery['main_url'], 'school.example')
                self.assertEqual(recovery['password'], '')
            secrets.pop('main_url')
            with patch.object(store, '_read', return_value=secrets):
                with self.assertRaises(store.CredentialError):
                    store.load_credentials(path)

    def test_origin_and_account_validation(self):
        for host in ('school.example/path', 'name@school.example', 'school.example:443', ''):
            with self.assertRaises((ValueError, store.CredentialError)):
                store.school_origin(host)
        self.assertEqual(store.school_origin('SCHOOL.EXAMPLE'), 'school.example')
        self.assertNotEqual(store.account_key(dict(main_url='school.example', username='a')),
                            store.account_key(dict(main_url='school.example', username='b')))

    def test_legacy_cleanup_only_removes_auth_files_inside_account_folder(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(secure_session.Path,'home',return_value=Path(folder)):
            root = Path(folder)/'.cache'/'smartschool'
            account = root/'student'; account.mkdir(parents=True)
            for name in ('cookies.txt','authenticated_user.yml','other.txt'):
                (account/name).touch()
            secure_session.remove_legacy_session('../student')
            self.assertTrue((account/'cookies.txt').exists())
            secure_session.remove_legacy_session('student')
            self.assertFalse((account/'cookies.txt').exists())
            self.assertFalse((account/'authenticated_user.yml').exists())
            self.assertTrue((account/'other.txt').exists())

    def test_lvs_cache_requires_the_current_account(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'data').mkdir()
            credentials = dict(main_url='school.example', username='old')
            snapshot = dict(account_key=store.account_key(credentials), lvs=dict(notes=[dict(id='1', title='PRIVATE')]))
            path = root/'data/planner_data.json'
            path.write_text(json.dumps(snapshot), encoding='utf-8')
            with patch.object(store, 'load_credentials', side_effect=lambda _: credentials.copy()), \
                    patch.object(Backend, '_job') as job, \
                    patch.object(store, 'smartschool_credentials') as load_session, \
                    patch('sync.TimeoutSmartschool') as session:
                backend = Backend(root)
                self.addCleanup(backend.shutdown)
                backend.openNote('1')
                job.assert_called_once()  # The fixture is a valid note for its original account.
                job.reset_mock()
                errors = []
                backend.error.connect(errors.append)
                credentials['username'] = 'new'
                backend.openNote('1')
                self.assertEqual(errors, ['Sync this account before opening LVS notes.'])
                job.assert_not_called()
                load_session.assert_not_called()
                session.assert_not_called()
                self.assertEqual(json.loads(path.read_text(encoding='utf-8')), snapshot)

    @unittest.skipUnless(os.name == 'nt', 'Windows DPAPI')
    def test_cookie_storage_is_encrypted_and_roundtrips(self):
        from requests.cookies import create_cookie
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'cookies.bin'
            jar = secure_session.EncryptedCookieJar(path)
            jar.set_cookie(create_cookie('session', 'fake-secret-cookie', domain='school.example', secure=True))
            jar.save(ignore_discard=True)
            self.assertNotIn(b'fake-secret-cookie', path.read_bytes())
            second = secure_session.EncryptedCookieJar(path)
            second.load(ignore_discard=True)
            cookie = next(iter(second))
            self.assertEqual(cookie.value, 'fake-secret-cookie')
            self.assertEqual(cookie.domain, 'school.example')
            self.assertTrue(cookie.secure)

    def test_login_body_cannot_be_redirected_to_another_origin(self):
        session = object.__new__(secure_session.SecureSmartschool)
        session.creds = SimpleNamespace(main_url='school.example')
        with self.assertRaises(ValueError):
            session._make_traced_request(Mock(), 'POST', 'https://evil.example/login', data='fake')
        with self.assertRaises(ValueError):
            session.rebuild_auth(SimpleNamespace(body='fake', url='https://evil.example/login'), None)

    def test_cached_login_reloads_user_from_authenticated_homepage(self):
        from smartschool import AppCredentials
        with tempfile.TemporaryDirectory() as folder, patch.object(secure_session, 'remove_legacy_session'):
            session = secure_session.SecureSmartschool(AppCredentials(username='fake', password='fake', mfa='REPLACE_ME', main_url='school.example'), Path(folder))
            response = Mock()
            def parse(value):
                self.assertIs(value, response)
                session.authenticated_user = {'id': 'current'}
            with patch.object(session, 'get', return_value=response) as get, patch.object(session, '_parse_login_information', side_effect=parse):
                self.assertEqual(session.authenticated_user, {'id': 'current'})
                self.assertEqual(session.authenticated_user, {'id': 'current'})
                get.assert_called_once_with('/')
            self.assertIsNone(session._authenticated_user_file)

    @unittest.skipUnless(os.name == 'nt', 'Windows DPAPI')
    def test_repair_keeps_an_encrypted_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'credentials.yml'
            original = b'password: [damaged-yaml'
            path.write_bytes(original)
            with patch.object(store, 'save_credentials') as save:
                setup_ui.write_credentials(path, 'student', 'new', 'school.example', recover=True)
                save.assert_called_once()
            from windows_security import unprotect
            recovery = path.with_suffix('.recovery.bin').read_bytes()
            self.assertNotIn(original, recovery)
            self.assertEqual(unprotect(recovery), original)

    def test_failed_atomic_save_preserves_old_state(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            task_state.set_note(root, 'task', 'original')
            with patch.object(task_state.os, 'replace', side_effect=OSError('disk error')):
                with self.assertRaises(OSError):
                    task_state.set_note(root, 'task', 'new')
            self.assertEqual(task_state.load_notes(root)['task'], 'original')
            with self.assertRaises(ValueError):
                task_state.set_note(root, 'task', 'x' * 5001)
            self.assertEqual(task_state.load_notes(root)['task'], 'original')

    def test_wrong_account_cache_is_not_rendered(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'data').mkdir()
            path = root/'data/planner_data.json'
            credentials = dict(main_url='school.example', username='new')
            snapshot = dict(account_key='other', todos=[dict(id='private-task', description='PRIVATE', due_date=date.today().isoformat())],
                            days=[], all_classes=[], lvs=dict(notes=[dict(id='1', title='PRIVATE')]))
            path.write_text(json.dumps(snapshot), encoding='utf-8')
            before = path.read_bytes()
            with patch.object(store, 'load_credentials', return_value=credentials), patch.object(Backend, '_job') as job:
                backend = Backend(root)
                self.addCleanup(backend.shutdown)
                self.assertEqual(backend.data, {})
                self.assertEqual(backend.tasks.rowCount(), 0)
                self.assertEqual(backend.tasks.all, [])
                self.assertEqual(backend.groups(5, ''), [])
                self.assertNotIn('PRIVATE', json.dumps([backend.data, backend.tasks.all, backend.groups(5, '')]))
                self.assertEqual(path.read_bytes(), before)
                job.assert_not_called()
                snapshot['account_key'] = store.account_key(credentials)
                path.write_text(json.dumps(snapshot), encoding='utf-8')
                backend.reload()
                self.assertEqual(backend.tasks.rowCount(), 1)
                self.assertEqual(backend.tasks.all[0]['title'], 'PRIVATE')
