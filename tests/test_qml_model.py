"""Focused memory-only prototype checks; deliberately local and gitignored."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'qml_app'))
from model import Tasks, Stopwatch
from fixtures import make_tasks, web_data


class ModelTests(unittest.TestCase):
    def test_shared_fixture_and_empty(self):
        self.assertEqual(make_tasks(0), [])
        self.assertEqual(len(make_tasks(1000)), 1000)
        self.assertEqual(len({t['taskId'] for t in make_tasks(1000)}), 1000)
        self.assertEqual([t['title'] for t in make_tasks()], [t['description'] for t in web_data(36)['todos']])
        with self.assertRaises(ValueError):
            make_tasks(999)

    def test_filter_and_state_survive_virtualization(self):
        model = Tasks(1000)
        self.assertTrue(model.change('synthetic-998', 'pinned', True))
        self.assertTrue(model.change('synthetic-998', 'note', 'Zoë 日本語 & <script>'))
        model.filter('zoË', 'All courses', 'All types', True)
        self.assertEqual([r['taskId'] for r in model.rows], ['synthetic-998'])
        self.assertTrue(model.change('synthetic-998', 'pinned', False))
        self.assertEqual(model.count, 0)
        model.filter('', 'All courses', 'All types', False)
        self.assertEqual(model.count, 997)
        self.assertEqual(model.all[998]['note'], 'Zoë 日本語 & <script>')
        model.filter('', 'Mathematics', 'Toets', False)
        self.assertEqual(model.count, 0)

    def test_boundary_rejection_does_not_destroy_note(self):
        model = Tasks()
        self.assertTrue(model.change('synthetic-0', 'note', 'a' * 5000))
        self.assertFalse(model.change('synthetic-0', 'note', 'a' * 5001))
        self.assertEqual(len(model.all[0]['note']), 5000)
        self.assertFalse(model.change('missing', 'done', True))
        self.assertFalse(model.change('synthetic-0', 'done', 'true'))
        self.assertFalse(model.change('synthetic-0', 'course', 'changed'))

    def test_grouping_completion_undo_and_missed(self):
        model = Tasks()
        for i in (11,23,35): model.all[i]['due'] = '2026-10-26'
        model.all[1]['due'] = '2026-10-23'
        model.all[2]['due'] = '2026-10-01'
        model.filter('', 'All courses', 'All types', False)
        self.assertNotIn('synthetic-1', [t['taskId'] for t in model.rows])
        model.setSection(1)
        self.assertEqual([t['taskId'] for t in model.rows], ['synthetic-1'])
        model.change('synthetic-1', 'done', True)
        self.assertEqual(model.count, 0)
        model.undo()
        self.assertEqual(model.count, 1)
        model.setSection(0)
        model.change('synthetic-0', 'done', True)
        self.assertNotIn('synthetic-0', [t['taskId'] for t in model.rows])
        model.expandCompleted(True)
        self.assertEqual(model.rows[-1]['group'], 'Completed')
        model.undo()
        self.assertFalse(model.all[0]['done'])
        model.change('synthetic-5', 'pinned', True)
        self.assertEqual(model.rows[0]['group'], 'Pinned')
        model.change('synthetic-5', 'pinned', True)
        model.undo()
        self.assertFalse(model.all[5]['pinned'])

    def test_dataset_reset_discards_undo(self):
        model = Tasks()
        model.change('synthetic-0', 'note', 'old draft')
        model.change('synthetic-0', 'note', 'new draft')
        model.dataset(36)
        self.assertFalse(model.undo())
        self.assertEqual(model.all[0]['note'], '')

    def test_summary_choices_and_group_counts_follow_data(self):
        model = Tasks(1000)
        self.assertEqual(sum(d['count'] for d in model.week), 39)
        self.assertIn('39 tasks', model.weekSummary)
        self.assertEqual(sum(model.groupCounts.values()), model.count)
        self.assertLessEqual(max(d['barHeight'] for d in model.week), 52)
        self.assertEqual({d['kind'] for d in model.week if d['count']}, {'Taak', 'Toets', 'Voorbereiding'})
        model.change('synthetic-0', 'done', True)
        self.assertIn('38 tasks', model.weekSummary)
        model.all[1]['course'] = 'Zoë 日本語'
        self.assertIn('Zoë 日本語', model.courses)
        model.filter('', 'Zoë 日本語', 'All types', False)
        self.assertEqual(model.groupCounts, {'Today': 1})
        self.assertEqual(model.kinds, ['All types', 'Taak', 'Toets', 'Voorbereiding'])
        self.assertEqual(model.all[0]['body'], web_data(1000)['todos'][0]['body'])
        model.dataset(0)
        self.assertEqual(model.courses, ['All courses'])
        self.assertEqual(model.kinds, ['All types'])
        self.assertIn('No tasks', model.weekSummary)
        self.assertTrue(all(d['barHeight'] == 4 for d in model.week))

    def test_single_task_summary_and_evaluation_weight(self):
        model = Tasks()
        model.all = model.all[:1]
        model.all[0]['kind'] = 'Productevaluatie'
        self.assertIn('1 task is due', model.weekSummary)
        self.assertIn('1 test or evaluation', model.weekSummary)
        self.assertIn('(1 item)', model.weekSummary)

    def test_completion_notifies_row_removal_without_reset(self):
        model = Tasks()
        removed, resets = [], []
        model.rowsRemoved.connect(lambda parent, first, last: removed.append((first,last)))
        model.modelReset.connect(lambda: resets.append(True))
        original = len(model.rows)
        self.assertTrue(model.change('synthetic-0','done',True))
        self.assertTrue(removed)
        self.assertFalse(resets)
        self.assertEqual(len(model.rows),original-1)
        self.assertTrue(model.all[0]['done'])
        self.assertIn('synthetic-0',model.completedIds)

    def test_local_changes_keep_persistent_rows_without_reset(self):
        from PySide6.QtCore import QPersistentModelIndex, Qt
        model = Tasks()
        task_id = model.rows[5]['taskId']
        anchor = QPersistentModelIndex(model.index(5))
        resets = []
        model.modelReset.connect(lambda: resets.append(True))
        model.change('synthetic-0', 'done', True)
        model.expandCompleted(True)
        model.expandCompleted(False)
        model.change('synthetic-9', 'pinned', True)
        model.change(task_id, 'note', 'Saved without rebuilding the page')
        model.undo()
        self.assertTrue(anchor.isValid())
        self.assertEqual(anchor.data(Qt.UserRole), task_id)
        self.assertEqual(len({row['taskId'] for row in model.rows}), len(model.rows))
        self.assertFalse(resets)

    def test_stopwatch_pause_resume_and_zero_epoch(self):
        now = [0.0]
        watch = Stopwatch(lambda: now[0])
        watch.toggle()
        now[0] = 12.75
        watch.toggle()
        now[0] = 100
        self.assertEqual(watch.seconds(), 12.75)
        watch.toggle()
        now[0] = 104.5
        self.assertEqual(watch.seconds(), 17.25)
        watch.reset()
        self.assertFalse(watch.running)
        self.assertEqual(watch.seconds(), 0)


if __name__ == '__main__':
    unittest.main()
