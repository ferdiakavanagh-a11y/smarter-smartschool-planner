import copy
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as Item
import unittest
from unittest.mock import Mock, patch

from requests.exceptions import Timeout
import planner_details as details
import sync


def http_error(status):
    return RuntimeError('private server message', Item(status_code=status))


class RemainingSyncTests(unittest.TestCase):
    def setUp(self):
        sync._optional_status.clear()
        sync._optional_hidden.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'data').mkdir()

    def prior(self):
        return {'generated_at': '2026-10-01T12:00:00',
                'results': [{'id': 'grade', 'date': '2026-10-01'}],
                'lvs': {'since': sync.lvs_since().isoformat(),
                        'notes': [{'id': 'note', 'date': '2026-10-01'}],
                        'absences': [{'id': 'absence', 'date': '2026-10-01'}]}}

    def retain(self, previous=None, result=None, lvs=None):
        return sync.retain_optional_sections(result or [], 'fetch error',
                    lvs or {'notes': [], 'absences': [], 'notes_error': '', 'absences_error': ''},
                    previous or {}, [])

    def test_transient_retention_and_repeated_stale_timestamps(self):
        sync._optional_status.update(results='transient', notes='transient', absences='transient')
        old = self.prior()
        results, message, lvs, status = self.retain(old)
        self.assertEqual(results, old['results'])
        self.assertEqual(lvs['notes'], old['lvs']['notes'])
        self.assertIn(old['generated_at'], message)
        self.assertEqual(status['notes']['status'], 'stale')
        again = dict(old, generated_at='2026-10-02T12:00:00', optional_section_status=status)
        self.assertEqual(self.retain(again)[3]['notes']['last_success_at'], old['generated_at'])

    def test_no_retention_for_new_account_year_permission_or_unknown_error(self):
        for reason in ('denied', 'invalid', 'unavailable', 'ok'):
            with self.subTest(reason=reason):
                sync._optional_status.update(results=reason, notes=reason, absences=reason)
                self.assertEqual(self.retain(self.prior())[0], [])
                self.assertEqual(self.retain(self.prior())[2]['notes'], [])
        sync._optional_status.update(results='transient', notes='transient')
        old = self.prior(); old['lvs']['since'] = '2000-09-01'
        self.assertEqual(self.retain(old)[0], [])
        self.assertEqual(self.retain({})[2]['notes'], [])

    def test_observed_private_or_deleted_rows_never_revive_after_partial_failure(self):
        old = self.prior()
        sync._optional_status.update(results='transient', notes='transient')
        sync._optional_hidden.update(results={'grade'}, notes={'note'})
        results, _, lvs, _ = self.retain(old, result=[{'id': 'new', 'date': '2026-10-03'}])
        self.assertEqual([row['id'] for row in results], ['new'])
        self.assertEqual(lvs['notes'], [])

    def test_lvs_partial_private_filter_and_http_denial(self):
        def notes(*a, **k):
            yield Item(item_id='note', private=True)
            raise Timeout()
        with patch.object(sync, 'StudentNotes', notes), patch.object(sync, 'StudentAbsences', side_effect=http_error(403)):
            lvs = sync.fetch_lvs(object())
        self.assertEqual(sync._optional_status['notes'], 'transient')
        self.assertEqual(sync._optional_status['absences'], 'denied')
        self.assertEqual(self.retain(self.prior(), lvs=lvs)[2]['notes'], [])
        self.assertEqual(self.retain(self.prior(), lvs=lvs)[2]['absences'], [])

    def test_dependency_download_errors_and_direct_status_are_classified(self):
        from requests import Response
        from smartschool._exceptions import SmartSchoolDownloadError, SmartSchoolJsonError
        for status, expected in ((503, 'transient'), (403, 'denied'), (404, 'unavailable')):
            response = Response(); response.status_code = status
            for cls in (SmartSchoolDownloadError, SmartSchoolJsonError):
                self.assertEqual(details.failure_kind(cls('safe', response)), expected)
            direct = RuntimeError(); direct.status_code = status
            self.assertEqual(details.failure_kind(direct), expected)

    def test_grades_continue_beyond_200_and_exact_page_boundary(self):
        for count in (200, 201, 251):
            rows = [{'identifier': str(i), 'date': '2026-10-01'} for i in range(count)]
            pages = [rows[i:i+50] for i in range(0, count, 50)]
            if count % 50 == 0:
                pages.append([])
            session = Mock(); session.json.side_effect = pages
            result, note = sync.fetch_results(session)
            self.assertEqual(len(result), count)
            self.assertFalse(note)
            self.assertEqual(session.json.call_count, len(pages))

    def test_grade_budget_limit_is_visible_and_repeating_pages_fail(self):
        rows = [{'identifier': str(i)} for i in range(50)]
        session = Mock(); session.json.return_value = rows
        result, note = sync.fetch_results(session, max_pages=1)
        self.assertEqual(len(result), 50)
        self.assertIn('incomplete', note)
        self.assertEqual(sync._optional_status['results'], 'truncated')
        warnings = []
        sync.retain_optional_sections(result, note, {'notes': [], 'absences': [], 'notes_error': '', 'absences_error': ''}, {}, warnings)
        self.assertTrue(any(w['source'] == 'results' and 'incomplete' in w['message'] for w in warnings))
        _, note = sync.fetch_results(session)
        self.assertTrue(note)
        self.assertEqual(session.json.call_count, 3)

    def test_grade_partial_timeout_denial_and_deleted_filter(self):
        rows = [{'identifier': str(i)} for i in range(49)] + [{'identifier': 'grade', 'deleted': True}]
        for exc, expected in ((Timeout(), 'transient'), (http_error(403), 'denied')):
            session = Mock(); session.json.side_effect = [rows, exc]
            result, note = sync.fetch_results(session)
            self.assertTrue(note)
            self.assertEqual(sync._optional_status['results'], expected)
            retained = self.retain(self.prior(), result=result)[0]
            self.assertNotIn('grade', [r['id'] for r in retained])

    def test_partial_schema_is_whole_source_failure(self):
        with patch.object(sync, 'PlannedElement', side_effect=[Item(), ValueError('private')]):
            with self.assertRaises(sync.PlannerSchemaError):
                list(sync.parse_planner_records([{'id': 'one'}, {'id': 'two'}], 'planner'))
        self.assertEqual(sync._planner_diagnostics['planner']['parsed'], 1)
        self.assertEqual(sync._planner_diagnostics['planner']['skipped'], 1)

    def test_timetable_partial_is_not_retried_with_narrower_filter(self):
        session = Mock(authenticated_user={'id': 'u'})
        session.json.return_value = [{}, {}]
        with patch.object(sync, 'PlannedElement', side_effect=[Item(), ValueError()]):
            with self.assertRaises(sync.PlannerSchemaError):
                sync.build_all_classes_planner_api(session, date.today(), date.today())
        self.assertEqual(session.json.call_count, 1)

    def test_run_schema_retention_and_permission_removal_are_account_scoped(self):
        today = date.today().isoformat()
        assignment = dict(type='Task', description='Read', body='Instructions', due_date=today,
                          due_date_corrected=False, warning=False, id='owned')
        event = dict(moment_id='task', source='planner_api', start='09:00', course='Math',
                     info={'assignments': [assignment]})
        creds = Item(main_url='school.smartschool.be', username='student', other_info={})
        session = Item(platform_id=1, authenticated_user={'id': 'u'})
        old = dict(account_key='approved', main_url=creds.main_url, user_id='u',
                   generated_at='2026-10-01T12:00:00', days=[{'date': today, 'events': [event]}],
                   todos=[dict(assignment, moment_id='task', element_source='planner_api', course='Math', posted_date=today)],
                   all_classes=[])
        for exc, same_account, retained in ((sync.PlannerSchemaError(), True, True),
                                           (http_error(403), True, False),
                                           (sync.PlannerSchemaError(), False, False)):
            snapshot = copy.deepcopy(old)
            if not same_account:
                snapshot['account_key'] = 'other-account'
            path = self.root/'data/planner_data.json'; path.write_text(json.dumps(snapshot))
            def lessons(*args):
                sync._fetch_errors['planner'] = exc
                sync._planner_diagnostics['planner'] = {'status': 'failed', 'skipped': 1}
                return []
            with patch.object(sync, 'ROOT', self.root), patch.object(sync, 'DATA_DIR', self.root/'data'), patch.object(sync, 'OUTPUT_FILE', path), \
                 patch.object(sync.credential_store, 'smartschool_credentials', return_value=creds), \
                 patch.object(sync.credential_store, 'account_key', return_value='approved'), \
                 patch.object(sync.credential_store, 'load_credentials', return_value={}), \
                 patch.object(sync, 'TimeoutSmartschool', return_value=session), \
                 patch.object(sync, 'build_lessons', side_effect=lessons), \
                 patch.object(sync, 'build_future_tasks', return_value=([], [])), \
                 patch.object(sync, 'build_all_classes_planner_api', return_value={}), \
                 patch.object(sync, 'fetch_results', return_value=([], '')), \
                 patch.object(sync, 'fetch_lvs', return_value={'notes': [], 'absences': [], 'notes_error': '', 'absences_error': ''}), \
                 patch.object(sync, 'fetch_assignment_types', return_value=[]):
                output = sync.run()
            self.assertEqual(bool(output['days']), retained)
            if retained:
                self.assertTrue(output['days'][0]['events'][0]['stale'])
                self.assertEqual(output['todos'][0]['body'], 'Instructions')

    def task(self, moment):
        return dict(id=None, moment_id=moment, element_source='legacy_agenda', course='Math',
                    type='Task', description='Read chapter 2', posted_date='2026-10-01', due_date='2026-10-02')

    def test_legacy_moment_identity_splits_already_collided_state(self):
        account = ['school', 'student']
        old = dict(self.task('moment-1'), id='ambiguous')
        semantic = [old[k] for k in ('course', 'type', 'description', 'posted_date')]
        key = hashlib.sha256(json.dumps([account, ['content', *semantic]], ensure_ascii=False).encode()).hexdigest()
        (self.root / 'data/task_identities.json').write_text(json.dumps({key: 'ambiguous'}))
        with patch.object(sync, 'ROOT', self.root), patch.object(sync, 'DATA_DIR', self.root/'data'):
            result = sync.assign_task_ids([self.task('moment-1'), self.task('moment-2')], [], {'todos': [old]}, account)
            again = sync.assign_task_ids([self.task('moment-2'), self.task('moment-1')], [], {'todos': result}, account)
        self.assertEqual(len(result), 2)
        self.assertEqual(len({t['id'] for t in result}), 2)
        self.assertTrue(all(t['id'] != 'ambiguous' for t in result))
        self.assertEqual({t['moment_id']: t['id'] for t in result}, {t['moment_id']: t['id'] for t in again})

    def test_unambiguous_legacy_identity_keeps_state(self):
        old = dict(self.task('one'), id='owned')
        with patch.object(sync, 'ROOT', self.root), patch.object(sync, 'DATA_DIR', self.root/'data'):
            result = sync.assign_task_ids([self.task('one')], [], {'todos': [old]}, ['s', 'u'])
        self.assertEqual(result[0]['id'], 'owned')

    def fetcher(self, session):
        return details.DetailFetcher(session, self.root/'route.json', 1, 'student')

    def test_detail_exact_identity_rejects_substrings_nested_titles_and_conflicts(self):
        session = Mock()
        fetcher = self.fetcher(session)
        for payload in ({'id': 'prefix-task'}, {'name': 'task title', 'publicInfo': 'task'},
                        {'wrapper': {'id': 'task'}}, {'id': 'task', 'identifier': 'other'},
                        {'id': 'task', 'publicInfo': ['wrong shape']}):
            session.json.return_value = payload
            self.assertIsNone(fetcher._get('/details/{id}', {'id': 'task', 'title': 'task title'}))
        session.json.return_value = {'id': 'task', 'publicInfo': ''}
        self.assertEqual(fetcher._get('/details/{id}', {'id': 'task'}), {'id': 'task', 'publicInfo': ''})
        session.json.return_value = {'id': 'task', 'publicInfo': '', 'wrapper': {'body': 'unrelated'}}
        self.assertNotIn('wrapper', fetcher._get('/details/{id}', {'id': 'task'}))

    def test_detail_budget_and_cancellation_prevent_requests(self):
        session = Mock()
        fetcher = self.fetcher(session)
        fetcher.template = '/details/{id}'
        fetcher.budget.cancel()
        self.assertIsNone(fetcher.fetch('task', 'planned-assignments', date.today()))
        self.assertEqual(fetcher.failures['task'], 'deferred')
        session.json.assert_not_called()
        budget = details.DetailBudget(max_requests=1)
        self.assertLessEqual(budget.timeout().total, 10)
        with self.assertRaises(TimeoutError):
            budget.timeout()
        with patch.object(details.time, 'monotonic', side_effect=[100, 146]):
            budget = details.DetailBudget()
            budget.timeout()
            with self.assertRaises(TimeoutError):
                budget.timeout()

    def test_denied_type_never_becomes_cache_eligible_deferred(self):
        session = Mock(); session.json.side_effect = http_error(403)
        fetcher = self.fetcher(session); fetcher.template = '/details/{id}'
        for i in range(5):
            fetcher.fetch(str(i), 'planned-assignments', date.today())
            self.assertEqual(fetcher.failures[str(i)], 'denied')
        self.assertEqual(session.json.call_count, 3)

    def test_legacy_detail_timeout_restores_but_denial_and_empty_clear(self):
        old = {'assignments': [{'description': 'Private instructions'}]}
        for exc in (Timeout(), http_error(403), ValueError()):
            with patch.object(sync, 'SmartschoolMomentInfos', side_effect=exc):
                info = sync.fetch_moment_info(Item(), 'moment', date.today(), 'Math', [], old)
                self.assertEqual(bool(info), isinstance(exc, Timeout))
        with patch.object(sync, 'SmartschoolMomentInfos', return_value=[]):
            self.assertIsNone(sync.fetch_moment_info(Item(), 'moment', date.today(), 'Math', [], old))

    def test_planner_detail_reuse_only_exact_identity_transient_failure(self):
        today = date.today()
        pe = Item(id='task', period=Item(date_time_from=datetime.now(), date_time_to=datetime.now(), deadline=False),
                  courses=[], locations=[], organisers=None, participants=None, name='Task',
                  planned_element_type='planned-assignments', assignment_type=None)
        prior = {('planner_api', 'task'): {'info': {'assignments': [{'body': 'Saved instructions', 'detail_fields': []}]}}}
        for reason in ('transient', 'deferred', 'denied', 'invalid'):
            fetcher = Mock(failures={'task': reason}); fetcher.fetch.return_value = None
            session = Mock(authenticated_user={'id': 'u'}); session.json.return_value = [{}]
            with patch.object(sync, 'PlannedElement', return_value=pe):
                output = sync.build_lessons_planner_api(session, today, today, [], fetcher, prior)
                a = output[today.isoformat()][0]['info']['assignments'][0]
                self.assertEqual(a['body'], 'Saved instructions' if reason in ('transient', 'deferred') else '')
            with patch.object(sync, 'PlannedElement', return_value=Item(**dict(vars(pe), id='other'))):
                output = sync.build_lessons_planner_api(session, today, today, [], fetcher, prior)
                self.assertEqual(output[today.isoformat()][0]['info']['assignments'][0]['body'], '')


if __name__ == '__main__':
    unittest.main()
