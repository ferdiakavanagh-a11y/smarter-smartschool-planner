import ast
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
import urllib.request

import app_errors
import credential_store
import updater


class AuditIntegrationTests(unittest.TestCase):

    def test_exception_values_are_not_copied_to_support_diagnostics(self):
        try:
            try:
                raise ValueError('private-student-text secret-password')
            except ValueError as cause:
                raise RuntimeError('api-key-example') from cause
        except RuntimeError as error:
            info = app_errors.explain(error)
        encoded = json.dumps(info)
        for secret in ('private-student-text', 'secret-password', 'api-key-example'):
            self.assertNotIn(secret, encoded)
        self.assertIn('ValueError', info['details'])
        self.assertIn('RuntimeError', info['details'])
        self.assertIn('test_audit_integration.py:', info['details'])

    def test_setup_opens_once_and_unlocks_after_failure(self):
        from test_qml_migration import MigrationTests
        case=MigrationTests();case.setUpClass();case.setUp();self.addCleanup(case.doCleanups)
        backend=case.backend
        with patch.object(threading,'Thread') as thread:
            self.assertTrue(backend.openSetup())
            self.assertFalse(backend.openSetup())
            thread.assert_called_once()
            backend._receive('setup',None,OSError('synthetic'))
            self.assertFalse(backend.busy)
            self.assertTrue(backend.openSetup())

    def test_lvs_result_is_discarded_if_account_changes_during_request(self):
        from test_qml_migration import MigrationTests
        case=MigrationTests();case.setUpClass();case.setUp();self.addCleanup(case.doCleanups)
        received=[];case.backend.detailReady.connect(lambda *args:received.append(args))
        case.credentials['username']='different'
        case.backend._receive('lvs:notes:1|'+case.data['account_key'],{'text':'PRIVATE'},None)
        self.assertEqual(received,[])

    def test_update_addresses_reject_before_opening(self):
        for address in ('http://github.com/file', 'https://raw.githubusercontent.com/attacker/file',
                        'https://github.com:444/file', 'https://name:pass@github.com/file',
                        'https://[broken', 'file:///test'):
            with self.subTest(address=address), patch.object(urllib.request, 'build_opener') as opener:
                with self.assertRaises(updater.UpdateError):
                    updater._open(address)
                opener.assert_not_called()
        for host in updater.ALLOWED_HOSTS:
            self.assertTrue(updater._url_ok('https://' + host + '/file'))

    def test_update_redirects_reject_before_following(self):
        request = urllib.request.Request('https://github.com/file')
        handler = updater._UpdateRedirectHandler()
        for address in ('http://github.com/file', 'https://example.com/file', 'http://127.0.0.1/private'):
            with self.assertRaises(updater.UpdateError):
                handler.redirect_request(request, None, 302, '', {}, address)
        redirected = handler.redirect_request(request, None, 302, '', {}, 'https://release-assets.githubusercontent.com/file')
        self.assertEqual(redirected.full_url, 'https://release-assets.githubusercontent.com/file')

    def test_release_response_size_and_shape_are_bounded(self):
        for value in (b'x' * (updater.MAX_RELEASE_BYTES + 1), b'[]', b'{"assets":{}}'):
            response = Mock()
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            response.read.return_value = value
            with patch.object(updater, '_open', return_value=response):
                with self.assertRaises(updater.UpdateError):
                    updater.check_for_update('2.1.2')
            response.read.assert_called_once_with(updater.MAX_RELEASE_BYTES + 1)


if __name__ == '__main__':
    unittest.main()
