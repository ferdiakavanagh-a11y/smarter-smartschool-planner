import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication
import credential_store
import task_state
from qml_app.backend import Backend


def snapshot(account):
    today = date.today().isoformat()
    return dict(account_key=account, main_url='school.example', user_id='1', generated_at='2026-10-27T12:00:00',
                todos=[dict(id='task-1', description='Quadratic functions', course='Mathematics', type='Toets', due_date=today, posted_date=today, body='Solve <b>the equation</b>.', detail_fields=[], attachments=[dict(name='Worksheet', url='https://school.example/file')])],
                days=[dict(date=today, events=[dict(moment_id='lesson-1', course='Mathematics', start='08:30', end='09:20', classroom='101', teacher='Demo', info=dict(assignments=[dict(id='task-1', description='Quadratic functions')]))])],
                all_classes=[], results=[dict(id='grade-1', name='Review', course='Mathematics', score=8, max=10, counts=True, feedback=['Well done']), dict(id='grade-2', course='Mathematics', score=1, max=100, counts=False)],
                lvs=dict(since='2026-09-01', notes=[dict(id='1', title='Progress', date=today)], absences=[dict(id='2', description='Authorised', date=today)]), warnings=[])


class MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        scratch = Path(__file__).resolve().parent/'check-temp'
        scratch.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root/'data').mkdir()
        self.credentials = dict(main_url='school.example', username='synthetic')
        self.mock = patch.object(credential_store, 'load_credentials', side_effect=lambda _: self.credentials.copy())
        self.mock.start()
        self.addCleanup(self.mock.stop)
        self.data = snapshot(credential_store.account_key(self.credentials))
        (self.root/'data/planner_data.json').write_text(json.dumps(self.data), encoding='utf-8')
        self.backend = Backend(self.root)
        self.addCleanup(self.backend.shutdown)

    def test_durable_edits_and_reload(self):
        model = self.backend.tasks
        self.assertEqual(model.rowCount(), 1)
        self.assertTrue(model.change('task-1', 'note', 'My draft'))
        self.assertTrue(model.change('task-1', 'pinned', True))
        self.assertTrue(model.change('task-1', 'done', True))
        self.backend.reload()
        self.assertEqual(model.all[0]['note'], 'My draft')
        self.assertTrue(model.all[0]['pinned'])
        self.assertTrue(model.all[0]['done'])
        self.assertEqual(model.rowCount(), 0)

    def test_failed_write_preserves_note(self):
        self.assertTrue(self.backend.tasks.change('task-1', 'note', 'Original'))
        with patch.object(task_state, 'set_note', side_effect=OSError('disk full')):
            self.assertFalse(self.backend.tasks.change('task-1', 'note', 'Unsaved draft'))
        self.assertEqual(self.backend.tasks.all[0]['note'], 'Original')
        self.assertEqual(task_state.load_notes(self.root)['task-1'], 'Original')

    def test_account_change_rejects_edits_and_cached_data(self):
        self.credentials['username'] = 'different'
        self.assertFalse(self.backend.tasks.change('task-1', 'done', True))
        self.assertFalse((self.root/'data/completed_tasks.json').exists())
        self.backend.reload()
        self.assertEqual(self.backend.tasks.rowCount(), 0)
        self.assertEqual(self.backend.groups(5, ''), [])

    def test_groups_weighting_and_hidden_read_state(self):
        self.assertEqual(self.backend.groups(2, '')[0]['items'][0]['assignments'][0]['id'], 'task-1')
        self.assertEqual(self.backend.groups(4, '')[0]['items'][0]['title'], '80%')
        self.assertTrue(self.backend.markRead('*'))
        self.assertEqual(set(task_state.load_settings(self.root)[self.backend.read_key()]), {'notes:1', 'absences:2'})
        self.assertFalse(self.backend.groups(5, 'Progress')[0]['items'][0]['unread'])

    def test_search_instructions_type_and_each_section(self):
        self.backend.tasks.filter('equation', 'All courses', 'All types', False)
        self.assertEqual(self.backend.tasks.rowCount(), 1)
        self.backend.tasks.filter('Toets', 'All courses', 'All types', False)
        self.assertEqual(self.backend.tasks.rowCount(), 1)
        self.assertTrue(self.backend.groups(2, 'Demo'))
        self.data['all_classes'] = self.data['days']
        self.backend.data = self.data
        self.assertTrue(self.backend.groups(3, 'Quadratic'))
        self.assertTrue(self.backend.groups(4, 'Well done'))
        self.assertTrue(self.backend.groups(5, 'Authorised'))

    def test_instructions_do_not_include_raw_api_fields(self):
        self.data['todos'][0]['detail_fields'] = [('assignmentType.name', 'Toets'), ('organisers.users[0].pictureUrl', 'https://school.example/avatar')]
        self.backend.data = self.data
        detail = self.backend.taskDetail('task-1')
        self.assertEqual(detail['body'], 'Solve the equation.')
        self.assertNotIn('organisers', detail['metadata'])

    def test_grade_symbols_format_and_rounding(self):
        self.data['results'] = [dict(id='color', course='Art', name='Practice', text='bullet_square_yellow', color='yellow', label='Developing'),
                                dict(id='score', course='Math', name='Review', score=22.5, max=30, percent=75, counts=True)]
        self.backend.data = self.data
        rows = [item for group in self.backend.groups(4, '') for item in group['items']]
        square = next(r for r in rows if r['id'] == 'color')
        grade = next(r for r in rows if r['id'] == 'score')
        self.assertEqual(square['square'], '#ffcc00')
        self.assertEqual(square['resultLabel'], 'Developing')
        self.assertNotIn('bullet_square', square['extra'])
        self.assertEqual(grade['extra'], '22,5 / 30')
        self.assertEqual(grade['percentText'], '75%')
        self.data['results'][1].update(score=14.5, max=20)
        self.assertEqual(self.backend.groups(4, '')[0]['items'][0]['title'], '73%')

    def test_schedule_assignments_keep_completion_and_written_date(self):
        item = self.backend.groups(2, '')[0]
        self.assertNotEqual(item['heading'], date.today().isoformat())
        self.assertEqual(item['items'][0]['assignments'][0]['kind'], 'Toets')
        self.assertFalse(item['items'][0]['assignments'][0]['done'])
        self.backend.tasks.change('task-1', 'done', True)
        self.assertTrue(self.backend.groups(2, '')[0]['items'][0]['assignments'][0]['done'])

    def test_lvs_unread_count_and_indicator(self):
        self.assertEqual(self.backend.unreadCount, 2)
        self.assertTrue(self.backend.groups(5, '')[0]['items'][0]['unread'])
        self.backend.markRead('absences:2')
        self.assertEqual(self.backend.unreadCount, 1)
        self.backend.markRead('*')
        self.assertEqual(self.backend.unreadCount, 0)

    def test_completion_feedback_saves_before_row_retirement(self):
        from PySide6.QtTest import QTest
        self.assertTrue(self.backend.tasks.complete('task-1'))
        self.assertIn('task-1', task_state.load_completed_ids(self.root))
        self.assertEqual(self.backend.tasks.rowCount(), 1)
        self.assertEqual(self.backend.tasks.groupCounts.get('Today',0),0)
        QTest.qWait(680)
        self.assertEqual(self.backend.tasks.rowCount(), 0)

    def test_feedback_timer_does_not_recomplete_after_undo(self):
        from PySide6.QtTest import QTest
        self.assertTrue(self.backend.tasks.complete('task-1'))
        self.assertTrue(self.backend.tasks.undo())
        QTest.qWait(680)
        self.assertNotIn('task-1', task_state.load_completed_ids(self.root))
        self.assertEqual(self.backend.tasks.rowCount(), 1)

    def test_setting_validation(self):
        self.assertTrue(self.backend.saveSettings(dict(renderingMode='performance', distortion=.25, textSize=1.15)))
        self.assertFalse(self.backend.saveSettings(dict(distortion=float('nan'))))
        self.assertFalse(self.backend.saveSettings(dict(password='no')))
        self.assertEqual(task_state.load_settings(self.root)['distortion'], .25)

    def test_links_and_body_are_safe(self):
        self.assertIn('Solve the equation', self.backend.taskDetail('task-1')['body'])
        self.assertFalse(self.backend.openExternal('file:///etc/passwd'))
        self.assertFalse(self.backend.openExternal('javascript:alert(1)'))

    def test_production_ai_badge_and_material_reminder_focus(self):
        self.data['todos'][0]['due_date_source'] = 'ai'
        self.backend.data = self.data
        self.assertIn('AI date', self.backend.taskBadges('task-1'))
        from qml_app.production_model import task_indicators
        indicator=task_indicators(dict(due_date_corrected=True))[0]
        self.assertEqual(indicator['icon'],'cal')
        self.assertTrue(self.backend.canFocus('task-1'))
        self.data['todos'][0]['type'] = 'Meenemen'
        self.assertFalse(self.backend.canFocus('task-1'))

    def test_task_links_preserve_native_planner_route_with_safe_fallback(self):
        from qml_app.production_model import planner_url
        data = dict(main_url='school.example', platform_id=148, user_id='7997')
        item = dict(moment_id='12345678-1234-1234-1234-123456789abc', element_source='planner_api', element_type='planned-tests')
        link = planner_url(data, item, '2026-10-27')
        self.assertIn('/planner/main/user/148_7997_0/2026-10-27/planned-tests/148/', link)
        item['moment_id'] = '../../secret'
        self.assertEqual(planner_url(data, item, '2026-10-27'), 'https://school.example/planner')

    def test_old_preferences_migrate_atomically_and_keep_read_state(self):
        task_state.set_setting(self.root, 'textSize', 'l')
        task_state.set_setting(self.root, 'glassLevel', 2)
        task_state.set_setting(self.root, self.backend.read_key(), ['notes:1'])
        self.backend._settings = task_state.load_settings(self.root)
        self.assertEqual(self.backend.settings['textSize'], 1.15)
        self.assertEqual(self.backend.settings['glassLevel'], 1)
        self.assertTrue(self.backend.saveSettings(dict(renderingMode='fancy')))
        saved = task_state.load_settings(self.root)
        self.assertEqual(saved['textSize'], 1.15)
        self.assertEqual(saved['qmlVersion'], 1)
        self.assertEqual(saved[self.backend.read_key()], ['notes:1'])

    def test_failed_preference_write_keeps_original_bytes(self):
        path = self.root/'data/ui_settings.json'
        path.write_text('{broken', encoding='utf-8')
        self.assertFalse(self.backend.saveSettings(dict(renderingMode='performance')))
        self.assertEqual(path.read_text(encoding='utf-8'), '{broken')

    def test_first_rendering_choice_remains_explicit(self):
        pending = self.root/'data/rendering_choice_pending'
        pending.touch()
        self.assertTrue(self.backend.saveSettings(dict(renderingMode='fancy')))
        self.assertTrue(pending.exists())
        self.assertFalse(self.backend.syncNow())
        self.assertTrue(self.backend.chooseRendering('performance'))
        self.assertFalse(pending.exists())

    def test_late_lvs_response_and_unknown_ids_do_not_disclose(self):
        received = []
        self.backend.detailReady.connect(lambda *args: received.append(args))
        with patch.object(self.backend, '_job') as job:
            self.backend.openNote('999')
            job.assert_not_called()
        self.credentials['username'] = 'different'
        self.backend._receive('lvs:notes:1|'+self.data['account_key'], dict(text='PRIVATE', fields={}), None)
        self.assertEqual(received, [])

    def test_queued_sync_failure_keeps_cached_tasks(self):
        failures = []
        self.backend.error.connect(failures.append)
        self.backend._jobs.add('sync')
        self.backend._receive('sync', None, OSError('offline'))
        self.assertFalse(self.backend.busy)
        self.assertEqual(self.backend.tasks.rowCount(), 1)
        self.assertTrue(failures)

    def test_update_verification_and_notice_precede_launch(self):
        import updater
        from PySide6.QtTest import QTest
        self.backend._update = dict(version='9.9.9', notes='Synthetic release')
        launched = []
        def launch(path, root):
            self.assertEqual(updater.load_update_notice(root, '9.9.9')['notes'], 'Synthetic release')
            launched.append(path)
        with patch.object(updater, 'download_and_verify', return_value=self.root/'installer.exe') as verify, patch.object(updater, 'launch_installer', side_effect=launch):
            self.assertTrue(self.backend.installUpdate())
            self.assertFalse(self.backend.installUpdate())
            for _ in range(100):
                QTest.qWait(10)
                if not self.backend.busy:
                    break
            verify.assert_called_once()
            self.assertEqual(launched, [self.root/'installer.exe'])
            self.assertFalse(self.backend.busy)


if __name__ == '__main__':
    unittest.main()
