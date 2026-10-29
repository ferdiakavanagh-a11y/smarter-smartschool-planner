import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import sync
import task_state


class DateCheckerTests(unittest.TestCase):
    def test_key_requirement_preferences_and_removal(self):
        with tempfile.TemporaryDirectory(dir='tests') as folder, patch('credential_store.load_credentials', return_value={}) as load:
            root = Path(folder)
            self.assertEqual(task_state.date_checker_state(root), {'mode':'local','geminiAvailable':False})
            with self.assertRaises(ValueError):
                task_state.set_setting(root, 'dateChecker', 'gemini')
            credentials = root / 'credentials.yml'
            credentials.touch()
            load.return_value = {'gemini_api_key': 'fake-test-key'}
            self.assertEqual(task_state.date_checker_state(root), {'mode':'gemini','geminiAvailable':True})
            task_state.set_setting(root,'dateChecker','local')
            self.assertEqual(task_state.date_checker_state(root)['mode'],'local')
            task_state.set_setting(root,'dateChecker','gemini')
            load.return_value = {'gemini_api_key': '   '}
            self.assertEqual(task_state.date_checker_state(root), {'mode':'local','geminiAvailable':False})
            self.assertNotIn('fake-test-key', str(task_state.load_settings(root)))
            with self.assertRaises(ValueError):
                task_state.set_setting(root,'dateChecker','unknown')

    def test_local_parser_does_not_call_gemini(self):
        reference = date(2026, 10, 15)
        with patch.object(sync,'_regex_active',True), patch.object(sync.gemini_dates,'extract_due_dates_batch') as gemini:
            result = sync.resolve_due_date_sync(None,'Tegen 16/10 afwerken',reference)
            self.assertEqual(result[0],'2026-10-16')
            sync.resolve_ai_pending([{'text':'No date','posted':reference,'entries':[]}],'fake-test-key')
            gemini.assert_not_called()

    def test_gemini_choice_uses_existing_ai_path(self):
        entry = {}
        pending = [{'text':'Deadline text','posted':date(2026,10,15),'entries':[entry]}]
        with patch.object(sync,'_regex_active',False), patch.object(sync.gemini_dates,'extract_due_dates_batch',return_value=([date(2026,10,16)],None)) as gemini, patch.object(sync.gemini_dates,'last_problem',None):
            sync.resolve_ai_pending(pending,'fake-test-key')
            gemini.assert_called_once()
        self.assertEqual(entry['due_date'],'2026-10-16')
        self.assertEqual(entry['due_date_source'],'ai')


if __name__ == '__main__':
    unittest.main()
