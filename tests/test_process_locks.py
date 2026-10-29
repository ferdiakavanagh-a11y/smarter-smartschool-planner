"""Process coordination regressions using temporary state and fake credentials only."""
import json
import multiprocessing
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import credential_store
from process_lock import file_lock
import setup_ui
import task_state


def hold_lock(path, acquired, release):
    with file_lock(Path(path)):
        acquired.set()
        if not release.wait(15):
            raise RuntimeError('Test holder was not released')


def note_writer(directory, task_id, started, read, release):
    original = task_state.load_notes

    def controlled(root, **kwargs):
        notes = original(root, **kwargs)
        read.set()
        if release is not None and not release.wait(15):
            raise RuntimeError('Test writer was not released')
        return notes

    with patch.object(task_state, 'load_notes', side_effect=controlled):
        started.set()
        task_state.set_note(Path(directory), task_id, task_id)


def credential_writer(path, key, started, read, release):
    original = credential_store.read_config

    def controlled(path):
        config = original(path)
        read.set()
        if release is not None and not release.wait(15):
            raise RuntimeError('Test writer was not released')
        return config

    def fake_save(path, config):
        config[key] = True
        path.write_text(json.dumps(config), encoding='utf-8')

    with patch.object(credential_store, 'read_config', side_effect=controlled), \
         patch.object(credential_store, 'save_credentials', side_effect=fake_save), \
         patch.object(setup_ui, 'restrict_permissions'):
        started.set()
        setup_ui.write_credentials(Path(path), 'synthetic', 'fake-password', 'school.example')


class ProcessLockTests(unittest.TestCase):
    def concurrent_writes(self, worker, destination, final_load):
        context = multiprocessing.get_context('spawn')
        one_started, two_started, one_read, two_read, release = [context.Event() for _ in range(5)]
        first = context.Process(target=worker, args=(str(destination), 'first', one_started, one_read, release))
        second = context.Process(target=worker, args=(str(destination), 'second', two_started, two_read, None))
        workers = []
        try:
            first.start()
            workers.append(first)
            self.assertTrue(one_read.wait(15))
            second.start()
            workers.append(second)
            self.assertTrue(two_started.wait(15))
            self.assertFalse(two_read.wait(0.3), 'contender must wait before reading state')
            release.set()
            for process in workers:
                process.join(15)
                self.assertEqual(process.exitcode, 0)
            values = final_load()
            self.assertIn('first', values)
            self.assertIn('second', values)
        finally:
            release.set()
            for process in workers:
                process.join(5)
                if process.is_alive():
                    process.terminate()
                    process.join(5)

    def test_two_process_state_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.concurrent_writes(note_writer, root, lambda: task_state.load_notes(root))

    def test_two_process_credential_editor_transactions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'credentials.yml'
            self.concurrent_writes(credential_writer, path, lambda: credential_store.read_config(path))

    def test_reentrant_same_path_and_nested_state_write(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with file_lock(root / 'data' / '.state.lock'):
                # Resolve an equivalent spelling to the same in-process lock.
                with file_lock(root / 'data' / '..' / 'data' / '.state.lock', timeout=0):
                    task_state.set_task_done(root, 'one', True)
            self.assertEqual(task_state.load_completed_ids(root), {'one'})

    @unittest.skipUnless(os.name == 'nt', 'case-insensitive Windows paths')
    def test_case_alias_reenters_same_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'case.lock'
            with file_lock(path):
                with file_lock(Path(str(path).upper()), timeout=0):
                    pass

    def test_setup_window_failure_releases_editor_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'credentials.yml'
            with patch.object(setup_ui, '_run_setup', side_effect=RuntimeError('synthetic')):
                with self.assertRaises(RuntimeError):
                    setup_ui.run_setup(path)
            with patch.object(setup_ui, '_run_setup', return_value=True):
                self.assertTrue(setup_ui.run_setup(path))

    def test_corrupt_config_can_still_be_replaced_after_recovery(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'credentials.yml'
            path.write_text('[broken', encoding='utf-8')
            secrets = dict(username='synthetic', password='fake', main_url='school.example', mfa='REPLACE_ME', gemini_api_key='')
            with patch.object(credential_store, '_api', return_value=Mock()), \
                 patch.object(credential_store, '_read', return_value=secrets), \
                 patch('windows_security.protect', return_value=b'encrypted-synthetic'), \
                 patch.object(setup_ui, 'restrict_permissions'):
                setup_ui.write_credentials(path, 'synthetic', 'fake', 'school.example', recover=True)
            self.assertEqual(path.with_suffix('.recovery.bin').read_bytes(), b'encrypted-synthetic')
            self.assertIn('vault_target', credential_store.read_config(path))

    def test_exception_releases_thread_and_os_locks(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'operation.lock'
            with self.assertRaises(ValueError):
                with file_lock(path):
                    raise ValueError('synthetic')
            completed = []
            def writer():
                with file_lock(path, timeout=0.2):
                    completed.append(True)
            thread = threading.Thread(target=writer)
            thread.start()
            thread.join(2)
            self.assertEqual(completed, [True])

    def test_process_contention_timeout_and_crash_release(self):
        context = multiprocessing.get_context('spawn')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'operation.lock'
            acquired, release = context.Event(), context.Event()
            process = context.Process(target=hold_lock, args=(str(path), acquired, release))
            try:
                process.start()
                self.assertTrue(acquired.wait(15))
                with self.assertRaises(TimeoutError):
                    with file_lock(path, timeout=0.1):
                        self.fail('contending process acquired the lock')
            finally:
                process.terminate()
                process.join(5)
            with file_lock(path, timeout=0.2):
                pass

    def test_second_editor_and_uninstall_refused_while_first_editor_open(self):
        context = multiprocessing.get_context('spawn')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'credentials.yml'
            acquired, release = context.Event(), context.Event()
            process = context.Process(target=hold_lock, args=(str(path.parent / 'data' / '.setup.lock'), acquired, release))
            try:
                process.start()
                self.assertTrue(acquired.wait(15))
                with patch.object(setup_ui, '_run_setup') as window, patch('tkinter.messagebox.showinfo') as info:
                    self.assertFalse(setup_ui.run_setup(path))
                    window.assert_not_called()
                    info.assert_called_once()
                with patch.object(credential_store, '_api') as vault:
                    with self.assertRaises(TimeoutError):
                        credential_store.clear_credentials(path)
                    vault.assert_not_called()
            finally:
                release.set()
                process.join(5)
                if process.is_alive():
                    process.terminate()
                    process.join(5)
            with patch.object(setup_ui, '_run_setup', return_value=True):
                self.assertTrue(setup_ui.run_setup(path))

    def test_latest_saved_target_cleaned_when_caller_has_stale_config(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'credentials.yml'
            stale = credential_store._prefix(path) + 'old'
            latest = credential_store._prefix(path) + 'latest'
            path.write_text(json.dumps({'vault_target': latest}), encoding='utf-8')
            secrets = dict(username='synthetic', password='fake', main_url='school.example', mfa='', gemini_api_key='')
            with patch.object(credential_store, '_api', return_value=Mock()), \
                 patch.object(credential_store, '_read', return_value=secrets), \
                 patch.object(credential_store, '_delete') as delete, \
                 patch('secure_session.remove_legacy_session'):
                credential_store.save_credentials(path, dict(secrets, vault_target=stale))
            delete.assert_called_once_with(latest)


if __name__ == '__main__':
    unittest.main()
