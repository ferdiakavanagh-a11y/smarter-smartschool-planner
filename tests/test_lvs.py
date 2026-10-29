import ast
import json
from datetime import date, datetime
from pathlib import Path
import tempfile
from types import SimpleNamespace as Item
import unittest
from unittest.mock import Mock, patch

import sync


class LvsTests(unittest.TestCase):
    def test_old_dependency_only_disables_lvs(self):
        with patch.object(sync, 'StudentNotes', None):
            result = sync.fetch_lvs(object())
            self.assertIn('0.12.0', result['notes_error'])
            self.assertIn('0.12.0', result['absences_error'])
            self.assertEqual(result['notes'], [])
            with self.assertRaises(RuntimeError):
                sync.fetch_lvs_note_detail(object(), '1')

    def test_school_year_boundary(self):
        for today, expected in [(date(2026, 8, 31), date(2025, 9, 1)), (date(2026, 9, 1), date(2026, 9, 1))]:
            class Calendar(date):
                @classmethod
                def today(cls):
                    return today
            with patch.object(sync, 'date', Calendar):
                self.assertEqual(sync.lvs_since(), expected)

    def note(self, id=1, private=False):
        return Item(item_id=id, private=private, title='Visible note', cat_name='Announcement', date=datetime(2026, 10, 1), author='Teacher')

    def test_overview_private_filter_and_independent_failures(self):
        notes = [self.note(), self.note(2, True)]
        with patch.object(sync, 'StudentNotes', return_value=notes), patch.object(sync, 'StudentAbsences', side_effect=RuntimeError('sensitive content')):
            overview = sync.fetch_lvs(object())
        self.assertEqual([n['id'] for n in overview['notes']], ['1'])
        self.assertEqual(overview['notes_error'], '')
        self.assertTrue(overview['absences_error'])
        self.assertNotIn('sensitive content', json.dumps(overview))
        absence = Item(absent_id=3, date=date(2026, 10, 2), code='Z', description='Illness', part_of_day='VM', info='')
        with patch.object(sync, 'StudentNotes', side_effect=RuntimeError()), patch.object(sync, 'StudentAbsences', return_value=[absence]):
            overview = sync.fetch_lvs(object())
        self.assertEqual(overview['absences'][0]['part'], 'VM')
        self.assertTrue(overview['notes_error'])

    def test_details_recheck_visibility_and_return_plain_text(self):
        factory = Mock()
        factory.return_value.get.return_value = Item(text='<script>plain text</script>', choice='Follow-up', fields={'Teacher':'Example'}, date=None, attachments=[Item(file_name='notes.pdf')])
        with patch.object(sync, 'StudentNotes', return_value=[self.note(1, True)]), patch.object(sync, 'StudentNoteDetails', factory):
            with self.assertRaises(ValueError):
                sync.fetch_lvs_note_detail(object(), '1')
            factory.assert_not_called()
        with patch.object(sync, 'StudentNotes', return_value=[self.note()]), patch.object(sync, 'StudentNoteDetails', factory):
            result = sync.fetch_lvs_note_detail(object(), '1')
        self.assertEqual(result['attachments'], [{'name':'notes.pdf'}])
        self.assertEqual(result['text'], '<script>plain text</script>')

    def test_bridge_rejects_ids_outside_synced_notes(self):
        from test_qml_migration import MigrationTests
        case=MigrationTests();case.setUpClass();case.setUp();self.addCleanup(case.doCleanups)
        with patch.object(case.backend,'_job') as job:
            case.backend.openNote('2');job.assert_not_called()
            case.backend.openNote('1');self.assertEqual(job.call_count,1)
            self.assertTrue(job.call_args.args[0].startswith('lvs:notes:1|'))


if __name__ == '__main__':
    unittest.main()
