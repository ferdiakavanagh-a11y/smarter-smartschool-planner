import json
import unittest
from requests import Response
from secure_session import SecureSmartschool


class AccountBootstrapTests(unittest.TestCase):
    def parse(self, script):
        session = object.__new__(SecureSmartschool)
        session._authenticated_user = None
        response = Response()
        response._content = script.encode()
        session._parse_login_information(response)
        return session._authenticated_user

    def test_json_bootstrap_without_jquery_extend(self):
        data = json.dumps({'vars': {'authenticatedUser': {'id': '123', 'name': 'Synthetic'}}})
        self.assertEqual(self.parse("<script>Object.assign(SMSC, JSON.parse('"+data+"'));</script>")['id'], '123')

    def test_legacy_extend_still_works(self):
        self.assertEqual(self.parse('<script>$.extend(true, SMSC, {vars: {"authenticatedUser":{"id":123}}});</script>')['id'], 123)

    def test_external_script_and_invalid_identity_are_not_used(self):
        for user in [None, [], {}, {'id': False}, {'id': ''}, {'id': []}]:
            with self.subTest(user=user):
                data = json.dumps({'vars': {'authenticatedUser': user}})
                self.assertIsNone(self.parse("<script>Object.assign(SMSC, JSON.parse('"+data+"'));</script>"))
        self.assertIsNone(self.parse('<script src="remote.js">$.extend(true,SMSC,{vars:{"authenticatedUser":{"id":123}}});</script>'))
