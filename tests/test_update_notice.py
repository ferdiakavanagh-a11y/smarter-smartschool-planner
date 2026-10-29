import json
import ast
import threading
import traceback
from types import SimpleNamespace
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import updater


class UpdateNoticeTests(unittest.TestCase):

    def test_restart_dispatch_and_once_only_acknowledgement(self):
        from PySide6.QtCore import QCoreApplication
        from qml_app.backend import Backend
        self.app=QCoreApplication.instance() or QCoreApplication([])
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory, patch('version.__version__','2.0.6'):
            root=Path(directory);updater.save_update_notice(root,{'version':'2.0.6','notes':'Features'})
            backend=Backend(root)
            try:
                backend.startUpdates();self.assertEqual(backend.notice['kind'],'release')
                self.assertEqual(backend.notice['text'],'Features')
                backend.dismissNotice();self.assertEqual(backend.notice,{})
                backend.startUpdates();self.assertEqual(backend.notice,{})
            finally:backend.shutdown()

    def test_verified_notes_saved_before_install_and_failed_install_not_announced(self):
        from test_qml_migration import MigrationTests
        from PySide6.QtTest import QTest
        case=MigrationTests();case.setUpClass();case.setUp();self.addCleanup(case.doCleanups)
        backend=case.backend;backend._update={'version':'9.9.9','notes':'Synthetic notes'}
        def launch(path,root):
            self.assertEqual(updater.load_update_notice(root,'9.9.9')['notes'],'Synthetic notes')
            raise OSError('synthetic installer launch failure')
        with patch.object(updater,'download_and_verify',return_value=case.root/'installer.exe'),patch.object(updater,'launch_installer',side_effect=launch):
            self.assertTrue(backend.installUpdate())
            for _ in range(100):
                QTest.qWait(10)
                if not backend.busy:break
            self.assertFalse(backend.busy)
            self.assertIsNone(updater.load_update_notice(case.root,'2.0.6'))

    def test_notice_survives_restart_and_is_consumed_only_for_installed_version(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            info = {"version": "2.0.6", "notes": "## Features\n- New menus"}
            updater.save_update_notice(root, info)
            self.assertIsNone(updater.load_update_notice(root, "2.0.5-beta"))
            self.assertFalse(updater.dismiss_update_notice(root, "2.0.5-beta"))
            self.assertEqual(updater.load_update_notice(root, "2.0.6"), info)
            self.assertTrue(updater.dismiss_update_notice(root, "2.0.6"))
            self.assertIsNone(updater.load_update_notice(root, "2.0.6"))
            updater.prepare_installed_notice(root, "2.0.6", "Bundled notes")
            self.assertIsNone(updater.load_update_notice(root, "2.0.6"))
            updater.prepare_installed_notice(root, "2.0.7", "Next release")
            self.assertEqual(updater.load_update_notice(root, "2.0.7")["notes"], "Next release")

    def test_old_installer_fallback_preserves_github_notes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            updater.prepare_installed_notice(root, "2.0.6", "Offline notes")
            self.assertEqual(updater.load_update_notice(root, "2.0.6")["notes"], "Offline notes")
            updater.save_update_notice(root, {"version": "2.0.7", "notes": "GitHub release body"})
            updater.prepare_installed_notice(root, "2.0.7", "Fallback")
            self.assertEqual(updater.load_update_notice(root, "2.0.7")["notes"], "GitHub release body")

    def test_corrupt_notice_does_not_block_startup(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            (root / "data").mkdir()
            for contents in ['{"broken":', '[]', 'null']:
                (root / "data" / "update_notice.json").write_text(contents)
                self.assertIsNone(updater.load_update_notice(root, "2.0.6"))

    def test_stable_release_updates_beta_and_retains_release_notes(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size=-1):
                return json.dumps({"tag_name": "v2.0.5", "body": "## New features", "assets": [
                    {"name": updater.INSTALLER_NAME, "browser_download_url": "https://github.com/installer"}
                ]}).encode()
        with patch("updater._open", return_value=Response()):
            info = updater.check_for_update("2.0.5-beta")
            self.assertEqual(info["version"], "2.0.5")
            self.assertEqual(info["notes"], "## New features")
            self.assertIsNone(updater.check_for_update("2.0.5"))
            self.assertIsNone(updater.check_for_update("2.0.6"))
        self.assertIsNone(updater.parse_version("garbage"))


if __name__ == "__main__":
    unittest.main()
