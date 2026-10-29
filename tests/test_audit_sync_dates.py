import contextlib
from datetime import date
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import ANY, Mock, patch

import dutch_dates
import gemini_dates as ai
import planner_details
import sync


class AuditSyncDatesTests(unittest.TestCase):
    def test_short_deadlines_are_not_dropped_before_ai(self):
        self.assertTrue(ai.looks_worth_asking('Tegen 1/2'))
        self.assertFalse(ai.looks_worth_asking(''))
        self.assertFalse(ai.looks_worth_asking('Lees tekst'))

    def test_same_day_local_deadline_is_not_marked_corrected(self):
        with patch.object(sync, '_regex_active', True):
            self.assertEqual(sync.resolve_due_date_sync(None, 'Deadline 19/10', date(2026, 10, 19)),
                             ('2026-10-19', False, 'regex', False))

    def test_deadline_formats_preserve_explicit_dates(self):
        for text, expected in [
            ('Due: 25/10', date(2026, 10, 25)),
            ('Due:25/10.', date(2026, 10, 25)),
            ('Deadline 2026-11-02', date(2026, 11, 2)),
            ('Tegen 25 september 2027', date(2027, 9, 25)),
            ('Due by 12 May 2027', date(2027, 5, 12)),
            ('À rendre le 12 mai 2027', date(2027, 5, 12)),
            ('Due by 12 August 2027', date(2027, 8, 12)),
        ]:
            with self.subTest(text=text):
                self.assertEqual(dutch_dates.extract_due_date(text, date(2026, 10, 19)), (expected, True))

    def test_signal_substrings_and_malformed_dates_are_ignored(self):
        for text in ('voorbeeld 25/10', 'Deadline 2026-13-02', 'Deadline 12/10/20267'):
            with self.subTest(text=text):
                self.assertEqual(dutch_dates.extract_due_date(text, date(2026, 10, 19)), (None, False))

    def test_corrupt_route_state_is_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'route.json'
            for data in ('[]', 'null', '{"template": 42}', 'broken'):
                with self.subTest(data=data):
                    path.write_text(data)
                    self.assertIsNone(planner_details.DetailFetcher(Mock(), path, 1, 'user').template)

    def test_detail_route_stays_within_approved_school(self):
        session = Mock(creds=SimpleNamespace(main_url='school.smartschool.be'))
        session.json.return_value = {'id': 'task/id', 'publicInfo': ''}
        with tempfile.TemporaryDirectory() as folder:
            fetcher = planner_details.DetailFetcher(session, Path(folder) / 'route.json', 1, 'user')
            ctx = {'id': 'task/id', 'title': 'A task'}
            for template in ('https://evil.invalid/{id}', '//evil.invalid/{id}', 'http://school.smartschool.be/{id}', '/\\evil.invalid/{id}', '/broken/{'):
                with self.subTest(template=template):
                    self.assertIsNone(fetcher._get(template, ctx))
            session.json.assert_not_called()
            self.assertEqual(fetcher._get('https://school.smartschool.be/details/{id}', ctx), {'id': 'task/id', 'publicInfo': ''})
            session.json.assert_called_once_with('https://school.smartschool.be/details/task%2Fid', timeout=ANY)

    def test_detail_diagnostics_omit_content_and_ids(self):
        session = Mock()
        session.json.side_effect = RuntimeError('PRIVATE CONTENT SECRET TOKEN')
        with tempfile.TemporaryDirectory() as folder:
            fetcher = planner_details.DetailFetcher(session, Path(folder) / 'route.json', 1, 'user')
            self.assertIsNone(fetcher._get('/details/{id}', {'id': 'PRIVATE-ID'}))
            self.assertEqual(fetcher.attempts, ['configured detail route -> RuntimeError'])

    def test_usage_state_shape_is_validated(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'usage.json'
            for models in (None, [], {'m': None}, {'m': {'recent': 'broken'}}, {'m': {'requests_today': 1, 'recent': [['bad', 1]], 'cooldown_until': 0, 'blocked_today': ''}}):
                with self.subTest(models=models):
                    path.write_text(json.dumps({'version': 2, 'day': ai._pacific_day(), 'models': models}))
                    limiter = ai.UsageLimiter(path)
                    limiter.wait_for_slot('m', 10)
                    limiter.record('m', 10)
                    self.assertEqual(limiter.state['models']['m']['requests_today'], 1)

    def test_valid_usage_limits_still_apply(self):
        limiter = ai.UsageLimiter(None)
        limiter.block_today('m', 'daily limit')
        with self.assertRaises(ai.LimitReached):
            limiter.wait_for_slot('m', 10)

    def test_cache_write_failure_preserves_existing_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'cache.json'
            path.write_text('{"old":null}')
            with patch('windows_security.os.replace', side_effect=OSError('disk unavailable')):
                ai._save_cache(path, {'new': None})
            self.assertEqual(json.loads(path.read_text()), {'old': None})

    def test_ai_startup_and_request_errors_are_private_and_visible(self):
        item = [('Tegen vrijdag afwerken', date(2026, 10, 19))]
        for target in ('_get_client', '_generate'):
            with self.subTest(target=target), patch.object(ai, '_get_client') as get_client, patch.object(ai, '_generate') as generate:
                (get_client if target == '_get_client' else generate).side_effect = RuntimeError('PRIVATE SECRET')
                _, note = ai.extract_due_dates_batch(item, 'fake-key')
                self.assertNotIn('PRIVATE SECRET', note)
                self.assertNotIn('PRIVATE SECRET', json.dumps(ai.last_problem))
                self.assertIsNotNone(ai.last_problem)

    def test_malformed_grade_fields_do_not_abort_or_emit_nonfinite_json(self):
        for graphic in ({'type': 'percentage', 'value': float('nan')},
                        {'type': 'percentage', 'value': float('inf')},
                        {'type': 'percentage', 'description': 'NaN / 10'},
                        {'type': 'percentage', 'description': '10 / Infinity'},
                        {'type': 'percentage', 'description': '1e308 / 1e-308'}):
            with self.subTest(graphic=graphic):
                result = sync.parse_result({'graphic': graphic, 'feedback': 42})
                self.assertIsNone(result['percent'])
                self.assertEqual(result['feedback'], [])
                json.dumps(result, allow_nan=False)

    def test_bad_grade_response_reports_failure_without_private_text(self):
        session = Mock()
        for response in (None, {}, RuntimeError('PRIVATE RESPONSE')):
            with self.subTest(response=type(response).__name__):
                session.json.side_effect = response if isinstance(response, Exception) else None
                session.json.return_value = response
                with contextlib.redirect_stderr(io.StringIO()) as captured:
                    result, note = sync.fetch_results(session)
                self.assertEqual(result, [])
                self.assertTrue(note)
                self.assertNotIn('PRIVATE RESPONSE', note + captured.getvalue())


if __name__ == '__main__':
    unittest.main()
