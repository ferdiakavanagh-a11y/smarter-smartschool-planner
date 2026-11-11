"""Clean-install route ordering must preserve explicit routes and failure policy."""
from datetime import date
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from requests.exceptions import Timeout
import planner_details as details


def denied():
    return RuntimeError('Synthetic failure', SimpleNamespace(status_code=403))


class DetailRouteStartupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name)/'route.json'
        self.session = Mock()

    def fetcher(self, custom=None):
        return details.DetailFetcher(self.session, self.path, 1, 'synthetic-user', custom)

    def test_previous_probe_version_negative_state_retries_canonical(self):
        self.path.write_text(json.dumps(dict(template=None, failed_on=date.today().isoformat(),
                                             probe_version=details.PROBE_VERSION-1)))
        self.session.json.return_value = {'id': 'task', 'publicInfo': 'Instructions'}
        result = self.fetcher().fetch('task', 'planned-assignments', date.today())
        self.assertEqual(result['publicInfo'], 'Instructions')
        self.assertEqual(self.session.json.call_args.args[0], '/planner/api/v1/planned-assignments/1/task')
        self.assertEqual(json.loads(self.path.read_text())['probe_version'], details.PROBE_VERSION)

    def test_current_negative_state_does_not_repeat_exhausted_probe_today(self):
        self.path.write_text(json.dumps(dict(template=None, failed_on=date.today().isoformat(),
                                             probe_version=details.PROBE_VERSION)))
        self.assertIsNone(self.fetcher().fetch('task', 'planned-assignments', date.today()))
        self.session.json.assert_not_called()

    def test_saved_route_has_precedence_and_is_kept_on_denial(self):
        for failure in (False, True):
            with self.subTest(denied=failure):
                original = json.dumps(dict(template='/saved-task/{id}', probe_version=2))
                self.path.write_text(original)
                self.session.reset_mock()
                self.session.json.side_effect = denied() if failure else None
                self.session.json.return_value = {'id': 'task', 'publicInfo': 'Instructions'}
                fetcher = self.fetcher()
                result = fetcher.fetch('task', 'planned-assignments', date.today())
                self.assertEqual(result is None, failure)
                self.assertEqual(self.session.json.call_count, 1)
                self.assertEqual(self.session.json.call_args.args[0], '/saved-task/task')
                self.assertEqual(self.path.read_text(), original)

    def test_custom_route_overrides_saved_route_without_rewriting_it(self):
        original = json.dumps(dict(template='/saved-task/{id}', probe_version=2))
        self.path.write_text(original)
        self.session.json.return_value = {'id': 'task', 'publicInfo': 'Instructions'}
        self.assertIsNotNone(self.fetcher('/explicit-task/{id}').fetch('task', 'planned-assignments', date.today()))
        self.assertEqual(self.session.json.call_count, 1)
        self.assertEqual(self.session.json.call_args.args[0], '/explicit-task/task')
        self.assertEqual(self.path.read_text(), original)

    def test_transient_canonical_failure_does_not_probe_legacy_routes_or_poison_state(self):
        self.session.json.side_effect = Timeout('Synthetic timeout')
        fetcher = self.fetcher()
        self.assertIsNone(fetcher.fetch('task', 'planned-assignments', date.today()))
        self.assertEqual(fetcher.failures['task'], 'transient')
        self.assertEqual(self.session.json.call_count, 1)
        self.assertFalse(self.path.exists())

    def test_canonical_identity_and_schema_must_pass_before_route_is_saved(self):
        for invalid in ({'id': 'other', 'publicInfo': 'Unrelated instructions'},
                        {'id': 'task', 'publicInfo': ['Invalid schema']}):
            with self.subTest(payload=invalid):
                self.session.reset_mock()
                self.session.json.side_effect = [invalid, denied()]
                fetcher = self.fetcher()
                self.assertIsNone(fetcher.fetch('task', 'planned-assignments', date.today()))
                self.assertIsNone(fetcher.template)
                self.assertEqual(self.session.json.call_count, 2)
                self.assertFalse(self.path.exists())


if __name__ == '__main__':
    unittest.main()
