import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import task_state

class NativePackagingTests(unittest.TestCase):
    def test_installer_includes_runtime_and_preserves_identity(self):
            build = Path('build_exe.bat').read_text()
            installer = Path('SmartschoolPlanner.iss').read_text()
            self.assertIn('--onedir', build)
            self.assertNotIn('--onefile', build)
            self.assertIn('dist\\SmartschoolPlanner\\_internal', build)
            self.assertIn('Source: "dist\\SmartschoolPlanner\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs', installer)
            self.assertIn('AppId={{B7C1E2A4-5D3F-4E8A-9A61-2F0C8D7E1B55}', installer)
            self.assertIn('SmartschoolPlanner-Setup', installer)
            self.assertNotIn('credentials.yml"; DestDir', installer)

    def test_installer_has_no_image_name_kill_or_setup_start_shutdown(self):
            source = Path('SmartschoolPlanner.iss').read_text()
            self.assertNotIn('taskkill', source.lower())
            self.assertNotIn('InitializeSetup', source)
            self.assertIn('CloseApplications=yes', source)
            self.assertIn('CloseApplicationsFilter={#AppExe}', source)

    def test_persistence_validation_and_failed_atomic_write(self):
            with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
                root = Path(directory)
                task_state.set_setting(root, 'style', 'clear')
                task_state.set_setting(root, 'renderingMode', 'performance')
                self.assertEqual(task_state.load_settings(root), {'style': 'clear', 'renderingMode': 'performance'})
                with self.assertRaises(ValueError):
                    task_state.set_setting(root, 'renderingMode', 'invalid')
                with patch('task_state.os.replace', side_effect=OSError('write failed')):
                    with self.assertRaises(OSError):
                        task_state.set_setting(root, 'renderingMode', 'fancy')
                self.assertEqual(task_state.load_settings(root)['renderingMode'], 'performance')
                self.assertEqual({path.name for path in (root / 'data').iterdir()},
                                 {'ui_settings.json', '.state.lock'}, 'temporary files cleaned up; process lock retained')
