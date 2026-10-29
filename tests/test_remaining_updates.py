import base64
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import updater


class Response(io.BytesIO):
    headers = {}


class RemainingUpdateTests(unittest.TestCase):
    def test_unconfigured_publisher_stops_before_network(self):
        with patch.object(updater, 'TRUSTED_SIGNER_SHA256', frozenset()), patch.object(updater, '_open') as network:
            with self.assertRaisesRegex(updater.UpdateError, 'paused'):
                updater.download_and_verify({'installer_url': 'https://github.com/file'})
            network.assert_not_called()

    def test_only_valid_pinned_certificate_is_accepted(self):
        certificate = b'synthetic-public-certificate'
        fingerprint = hashlib.sha256(certificate).hexdigest()
        for status, pinned in [('Valid', True), ('NotSigned', True), ('HashMismatch', True), ('UnknownError', True), ('Valid', False)]:
            response = SimpleNamespace(stdout=json.dumps({'status': status, 'certificate': base64.b64encode(certificate).decode()}))
            with self.subTest(status=status, pinned=pinned), patch.object(updater, 'TRUSTED_SIGNER_SHA256', frozenset([fingerprint] if pinned else ['other'])), \
                 patch.object(updater.subprocess, 'run', return_value=response) as run:
                if status == 'Valid' and pinned:
                    updater.verify_installer_signature(Path("publisher's.exe"))
                else:
                    with self.assertRaises(updater.UpdateError):
                        updater.verify_installer_signature(Path('installer.exe'))
                script = base64.b64decode(run.call_args.args[0][-1]).decode('utf-16-le')
                self.assertIn('Get-AuthenticodeSignature -LiteralPath', script)
                self.assertEqual(run.call_args.kwargs['timeout'], 30)

    @unittest.skipUnless(os.name == 'nt', 'Windows signature inspection')
    def test_windows_rejects_real_unsigned_binary(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'unsigned.exe'
            path.write_bytes(b'MZ\0synthetic-not-a-program')
            with patch.object(updater, 'TRUSTED_SIGNER_SHA256', frozenset(['not-a-real-publisher'])):
                with self.assertRaises(updater.UpdateError):
                    updater.verify_installer_signature(path)

    def test_download_records_cleanup_ownership_and_signature_failure_removes_files(self):
        content = b'MZ\0synthetic-not-a-program'
        info = {'installer_url': 'https://github.com/file', 'digest': hashlib.sha256(content).hexdigest()}
        real_mkdtemp = tempfile.mkdtemp
        with tempfile.TemporaryDirectory() as folder:
            def make_folder(**kwargs):
                return real_mkdtemp(dir=folder, **kwargs)
            with patch.object(updater, 'TRUSTED_SIGNER_SHA256', frozenset(['test'])), \
                 patch.object(updater.tempfile, 'mkdtemp', side_effect=make_folder), \
                 patch.object(updater, '_open', side_effect=lambda *args: Response(content)), \
                 patch.object(updater, 'verify_installer_signature') as verify, \
                 patch.object(updater.tempfile, 'gettempdir', return_value=folder):
                path = updater.download_and_verify(info)
                verify.assert_called_once_with(path)
                self.assertIsNotNone(updater._cleanup_token(path))
                (path.parent/'.ssp-owner').write_text('changed')
                self.assertIsNone(updater._cleanup_token(path))
                # No path ownership from a marker alone: the process must have created it.
                updater._download_tokens.pop(path)
                self.assertIsNone(updater._cleanup_token(path))
                verify.side_effect = updater.UpdateError('unsigned')
                with self.assertRaises(updater.UpdateError):
                    updater.download_and_verify(info)
                self.assertEqual(list(Path(folder).iterdir()), [path.parent])

    def test_launch_rechecks_signature_before_spawning(self):
        with patch.object(updater, 'verify_installer_signature', side_effect=updater.UpdateError('untrusted')), \
             patch.object(updater.subprocess, 'Popen') as spawn:
            with self.assertRaises(updater.UpdateError):
                updater.launch_installer(Path('bad.exe'))
            spawn.assert_not_called()

    def test_owned_monitor_cleanup_is_exact_and_nonrecursive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root/'ssp-update-test'/updater.INSTALLER_NAME
            path.parent.mkdir()
            path.write_bytes(b'MZ')
            (path.parent/'.ssp-owner').write_text('token')
            updater._download_tokens[path] = 'token'
            worker = Mock()
            def launch(*args, **kwargs):
                (root/'data/install_result.json').write_text('{"status":"running"}')
                return worker
            with patch.object(updater, 'verify_installer_signature'), patch.object(updater.tempfile, 'gettempdir', return_value=folder), \
                 patch.object(updater.subprocess, 'Popen', side_effect=launch) as spawn:
                updater.launch_installer(path, root)
            script = base64.b64decode(spawn.call_args.args[0][-1]).decode('utf-16-le')
            self.assertIn('ReparsePoint', script)
            self.assertIn("'token'", script)
            self.assertIn('[IO.Directory]::Delete(', script)
            self.assertNotIn('-Recurse', script)
            if os.name == 'nt':
                # Execute only the monitor logic; the installer launcher is a harmless stub.
                stub = "function Start-Process {param($FilePath,$ArgumentList,$WindowStyle,[switch]$PassThru,[switch]$Wait); [pscustomobject]@{ExitCode=0}}; "
                encoded = base64.b64encode((stub + script).encode('utf-16-le')).decode('ascii')
                command = [str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'),
                           '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded]
                subprocess.run(command, timeout=20, check=True, capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW)
                self.assertFalse(path.parent.exists(), 'owned installer and directory removed after completion')
                self.assertEqual(json.loads((root/'data/install_result.json').read_text(encoding='utf-8-sig'))['status'], 'ok')
            updater._download_tokens.pop(path)


if __name__ == '__main__':
    unittest.main()
