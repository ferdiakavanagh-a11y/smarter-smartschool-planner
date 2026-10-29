"""Offline transport regressions; no account storage or network access."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from requests import Request, Session
from smartschool import Smartschool
from secure_session import SecureSmartschool


class SessionRedirectSecurityTests(unittest.TestCase):
    def session(self):
        session = object.__new__(SecureSmartschool)
        Session.__init__(session)
        session.trust_env = False
        session.creds = SimpleNamespace(main_url='school.example')
        return session

    def test_cookie_bearing_get_cannot_downgrade_to_http(self):
        session = self.session()
        session.cookies.set('session', 'synthetic-cookie', domain='school.example', secure=False)
        request = session.prepare_request(Request('GET', 'http://school.example/planner'))
        self.assertIn('session=synthetic-cookie', request.headers['Cookie'])
        self.assertIsNone(request.body)
        with patch.object(Smartschool, 'rebuild_auth') as parent:
            with self.assertRaisesRegex(ValueError, 'insecure session redirect'):
                session.rebuild_auth(request, SimpleNamespace())
            parent.assert_not_called()

    def test_https_cross_origin_get_keeps_normal_requests_auth_handling(self):
        session = self.session()
        request = Request('GET', 'https://resources.example/attachment').prepare()
        with patch.object(Smartschool, 'rebuild_auth') as parent:
            session.rebuild_auth(request, SimpleNamespace())
            parent.assert_called_once()

    def test_https_cross_origin_post_body_is_still_rejected(self):
        session = self.session()
        request = Request('POST', 'https://resources.example/login', data='synthetic').prepare()
        with patch.object(Smartschool, 'rebuild_auth') as parent:
            with self.assertRaisesRegex(ValueError, 'unapproved address'):
                session.rebuild_auth(request, SimpleNamespace())
            parent.assert_not_called()


if __name__ == '__main__':
    unittest.main()
