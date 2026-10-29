import unittest
from unittest.mock import Mock
from requests import Response
from app_errors import SyncError, explain
from secure_session import SecureSmartschool


class AccountResponseTests(unittest.TestCase):
    def test_failure_reports_only_safe_response_structure(self):
        for url, page in [('https://school.example/', '/'), ('https://school.example/login', '/login'), ('https://school.example/private/student-secret?token=secret', 'other')]:
            with self.subTest(page=page):
                session = object.__new__(SecureSmartschool)
                session._authenticated_user = None
                response = Response()
                response.status_code = 200
                response.url = url
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
                response._content = b'<html>private name and cookie-secret</html>'
                session.get = Mock(return_value=response)
                session._parse_login_information = Mock()
                with self.assertRaises(SyncError) as caught:
                    _ = session.authenticated_user
                info = explain(caught.exception)
                self.assertIn('page='+page, info['details'])
                self.assertNotIn('private', info['details'])
                self.assertNotIn('secret', info['details'])
                self.assertNotIn('school.example', info['details'])
                self.assertNotIn("didn't accept", info['message'])
                session.get.assert_called_once_with('/')

    def test_old_error_does_not_claim_password_was_rejected(self):
        self.assertNotIn("didn't accept", explain(ValueError('Could not retrieve authenticated user information'))['message'])
