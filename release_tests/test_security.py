import ast
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import credential_store as store
import secure_session
import setup_ui
import task_state


class SecurityTests(unittest.TestCase):
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
        tree=ast.parse(Path('desktop_app.py').read_text(encoding='utf-8'))
        api=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Api')
        method=next(n for n in api.body if isinstance(n,ast.FunctionDef) and n.name=='lvs_note_detail')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'planner.json'
            path.write_text(json.dumps({'account_key':'old','lvs':{'notes':[{'id':'1'}]}}))
            namespace=dict(DATA_FILE=path,CREDS_FILE=Path(folder)/'credentials.yml',json=json)
            exec(compile(ast.Module(body=[method],type_ignores=[]),'desktop_app.py','exec'),namespace)
            creds=SimpleNamespace(main_url='school.example',username='new')
            with patch.object(store,'smartschool_credentials',return_value=creds), patch('sync.TimeoutSmartschool') as session:
                self.assertIn('error',namespace['lvs_note_detail'](None,'1'))
                session.assert_not_called()

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
        import planner_html
        tree = ast.parse(Path('desktop_app.py').read_text(encoding='utf-8'))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'load_cached_html')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = root / 'planner_data.json'
            data.write_text(json.dumps(dict(account_key='other', todos=[dict(description='PRIVATE')], days=[], all_classes=[])))
            namespace = dict(ROOT=root, DATA_FILE=data, CREDS_FILE=root/'credentials.yml', sys=SimpleNamespace(argv=[]),
                             task_state=task_state, planner_html=planner_html, json=json)
            exec(compile(ast.Module(body=[function], type_ignores=[]), 'desktop_app.py', 'exec'), namespace)
            with patch.object(store, 'load_credentials', return_value=dict(main_url='school.example', username='new')):
                html = namespace['load_cached_html']()
            self.assertNotIn('PRIVATE', html)
