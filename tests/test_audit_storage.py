"""Isolated storage regressions: synthetic credentials and temporary files only."""
import ctypes
import json
import multiprocessing
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import credential_store
import secure_session
import setup_ui
import task_state


def _concurrent_note_writer(directory, task_id, started, read, release, bypass_lock=False):
    original_load = task_state.load_notes

    def controlled_load(root, **kwargs):
        notes = original_load(root, **kwargs)
        read.set()
        if release is not None and not release.wait(15):
            raise RuntimeError('Test writer was not released')
        return notes

    writer = task_state.set_note.__wrapped__ if bypass_lock else task_state.set_note
    with patch.object(task_state, 'load_notes', side_effect=controlled_load):
        started.set()
        writer(Path(directory), task_id, task_id)


class StorageAuditTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows named mutex')
    def test_two_process_note_updates_preserve_both_writes(self):
        context = multiprocessing.get_context('spawn')
        with tempfile.TemporaryDirectory() as directory:
            started_one, started_two = context.Event(), context.Event()
            read_one, read_two, release_one = context.Event(), context.Event(), context.Event()
            first = context.Process(target=_concurrent_note_writer, args=(directory, 'first', started_one, read_one, release_one))
            second = context.Process(target=_concurrent_note_writer, args=(directory, 'second', started_two, read_two, None))
            workers = []
            try:
                first.start()
                workers.append(first)
                self.assertTrue(read_one.wait(15), 'first process reached its state read')
                second.start()
                workers.append(second)
                self.assertTrue(started_two.wait(15), 'second process started its write')
                self.assertFalse(read_two.wait(0.5), 'second process must wait before reading the same state')
                release_one.set()
                for worker in workers:
                    worker.join(15)
                    self.assertEqual(worker.exitcode, 0)
                self.assertEqual(task_state.load_notes(Path(directory)), {'first': 'first', 'second': 'second'})
            finally:
                release_one.set()
                for worker in workers:
                    worker.join(5)
                    if worker.is_alive():
                        worker.terminate()
                        worker.join(5)

    def test_session_preserves_password_whitespace(self):
        from smartschool import AppCredentials
        with tempfile.TemporaryDirectory() as directory, patch.object(secure_session, 'remove_legacy_session'):
            credentials = AppCredentials(username='synthetic', password=' synthetic ', main_url='school.example', mfa='REPLACE_ME')
            session = secure_session.SecureSmartschool(credentials, Path(directory))
            self.assertEqual(session.creds.password, ' synthetic ')

    def test_state_mutations_preserve_corrupt_files(self):
        cases = (
            ('completed_tasks.json', lambda root: task_state.set_task_done(root, 'new', True)),
            ('pinned_tasks.json', lambda root: task_state.set_task_pinned(root, 'new', True)),
            ('task_notes.json', lambda root: task_state.set_note(root, 'new', 'note')),
            ('ui_settings.json', lambda root: task_state.set_setting(root, 'style', 'clear')),
        )
        for name, mutate in cases:
            for damaged in (b'{damaged', b'null', b'\xff'):
                with self.subTest(name=name, damaged=damaged), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    path = root / 'data' / name
                    path.parent.mkdir()
                    path.write_bytes(damaged)
                    with self.assertRaisesRegex(ValueError, 'Existing data was kept'):
                        mutate(root)
                    self.assertEqual(path.read_bytes(), damaged)

    def test_bad_completion_shapes_do_not_break_display(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / 'data' / 'completed_tasks.json'
            path.parent.mkdir()
            for value in (None, 5, 'abc', {'fake': True}, [['nested']], ['ok', 9]):
                with self.subTest(value=value):
                    path.write_text(json.dumps(value), encoding='utf-8')
                    self.assertEqual(task_state.load_completed_ids(root), set())
                    with self.assertRaises(ValueError):
                        task_state.set_task_done(root, 'new', True)

    def test_unreadable_notes_cannot_replace_existing_notes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_state.set_note(root, 'first', 'keep me')
            with patch.object(Path, 'read_text', side_effect=PermissionError('denied')):
                self.assertEqual(task_state.load_notes(root), {})
                with self.assertRaises(ValueError):
                    task_state.set_note(root, 'second', 'new')
            self.assertEqual(task_state.load_notes(root), {'first': 'keep me'})

    def test_malformed_note_values_refuse_saves_and_migration(self):
        for value in (None, False, 42, ['unfinished note'], {'text': 'unfinished note'}):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                task_state.set_task_done(root, 'old', True)
                task_state.set_task_pinned(root, 'old', True)
                path = root / 'data' / 'task_notes.json'
                path.write_text(json.dumps({'old': value, 'valid': 'Keep me'}), encoding='utf-8')
                before = {name: (path.parent / name).read_bytes() for name in
                          ('task_notes.json', 'completed_tasks.json', 'pinned_tasks.json')}
                self.assertEqual(task_state.load_notes(root)['valid'], 'Keep me')
                for mutate in (lambda: task_state.set_note(root, 'new', 'New note'),
                               lambda: task_state.migrate_task_ids(root, {'old': 'new'})):
                    with self.assertRaisesRegex(ValueError, 'Existing data was kept'):
                        mutate()
                    self.assertEqual({name: (path.parent / name).read_bytes() for name in before}, before)

    def test_migration_does_not_write_any_state_if_a_source_is_corrupt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_state.set_task_done(root, 'old', True)
            task_state.set_task_pinned(root, 'old', True)
            notes = root / 'data' / 'task_notes.json'
            notes.write_bytes(b'{damaged')
            before = {path.name: path.read_bytes() for path in notes.parent.iterdir()}
            with self.assertRaises(ValueError):
                task_state.migrate_task_ids(root, {'old': 'new'})
            self.assertEqual({path.name: path.read_bytes() for path in notes.parent.iterdir()}, before)

    def test_settings_use_durable_atomic_write(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(task_state.os, 'fsync') as flush:
            root = Path(directory)
            task_state.set_setting(root, 'style', 'clear')
            flush.assert_called_once()
            self.assertEqual(task_state.load_settings(root), {'style': 'clear'})

    def test_impossible_birthdates_are_rejected(self):
        for value in ('2026-02-29', '2026-04-31', '0000-01-01', '31/02/2008'):
            with self.subTest(value=value):
                self.assertIsNotNone(setup_ui.normalize_security(value)[1])
        for value in ('2024-02-29', '29/02/2024', '20240229', '2024.02.29'):
            self.assertEqual(setup_ui.normalize_security(value), ('2024-02-29', None))
        self.assertEqual(setup_ui.normalize_security('JBSWY3DPEHPK3PXP'), ('JBSWY3DPEHPK3PXP', None))

    def test_falsey_non_mapping_configuration_requires_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'credentials.yml'
            for value in ('false', '0', '[]', '""'):
                with self.subTest(value=value):
                    path.write_text(value, encoding='utf-8')
                    with self.assertRaises(credential_store.CredentialError):
                        credential_store.read_config(path)
            path.write_text('', encoding='utf-8')
            self.assertEqual(credential_store.read_config(path), {})

    def test_failed_legacy_cleanup_does_not_leave_previous_vault_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'credentials.yml'
            old_target = credential_store._prefix(path) + 'old'
            secrets = dict(username='synthetic', password='synthetic', main_url='school.example', mfa='', gemini_api_key='')
            api = Mock()
            api.CredWriteW.return_value = True
            with patch.object(credential_store, '_api', return_value=api), \
                 patch.object(credential_store, '_read', return_value=secrets), \
                 patch.object(credential_store, '_delete') as delete, \
                 patch.object(secure_session, 'remove_legacy_session', side_effect=PermissionError('denied')):
                credential_store.save_credentials(path, dict(secrets, vault_target=old_target))
            delete.assert_called_once_with(old_target)
            config = credential_store.read_config(path)
            self.assertNotEqual(config['vault_target'], old_target)
            self.assertNotIn('password', config)

    def test_uninstall_deletes_vault_entry_even_if_legacy_cleanup_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'credentials.yml'
            target = credential_store._prefix(path) + 'old'
            record = credential_store._Credential(Type=1, TargetName=target)
            pointer_type = ctypes.POINTER(credential_store._Credential)
            entries = (pointer_type * 1)(ctypes.pointer(record))

            def enumerate_entries(_filter, _flags, count, output):
                ctypes.cast(count, ctypes.POINTER(credential_store.wintypes.DWORD))[0] = 1
                ctypes.cast(output, ctypes.POINTER(ctypes.POINTER(pointer_type)))[0] = entries
                return True

            api = Mock()
            api.CredEnumerateW.side_effect = enumerate_entries
            with patch.object(credential_store, '_api', return_value=api), \
                 patch.object(credential_store, '_read', return_value={'username': 'synthetic'}), \
                 patch.object(credential_store, '_delete') as delete, \
                 patch.object(secure_session, 'remove_legacy_session', side_effect=PermissionError('denied')):
                credential_store.clear_credentials(path)
            delete.assert_called_once_with(target)


if __name__ == '__main__':
    unittest.main()
