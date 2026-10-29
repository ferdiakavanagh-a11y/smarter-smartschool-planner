from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import planner_details
import sync
import task_state


def task(server, description='Same title'):
    return dict(id=None, course='Math', type='Task', description=description, posted_date='2026-10-15',
                due_date='2026-10-16', element_source='planner_api', moment_id=server, source='lesson')


class SyncTests(unittest.TestCase):
    def test_different_server_task_does_not_inherit_state(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'data').mkdir()
            old = dict(task('A'), id='existing')
            task_state.set_task_done(root, 'existing', True)
            with patch.object(sync, 'ROOT', root), patch.object(sync, 'DATA_DIR', root/'data'):
                result = sync.assign_task_ids([task('A'), task('B')], [], dict(todos=[old]), ['school','student'])
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['id'], 'existing')
            self.assertNotEqual(result[1]['id'], 'existing')
            self.assertNotIn(result[1]['id'], task_state.load_completed_ids(root))

    def test_identity_survives_deadline_change_and_legacy_migration(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'data').mkdir()
            old = dict(task('A'), id='old')
            current = dict(task('A'), due_date='2026-11-01')
            with patch.object(sync, 'ROOT', root), patch.object(sync, 'DATA_DIR', root/'data'):
                result = sync.assign_task_ids([current], [], dict(todos=[old]), ['school','student'])
                second = sync.assign_task_ids([dict(current,due_date='2026-11-02')], [], dict(todos=[]), ['school','student'])
            self.assertEqual(result[0]['id'], 'old')
            self.assertEqual(second[0]['id'], 'old')

    def test_existing_bad_registry_collision_is_split(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'data').mkdir()
            old=dict(task('A'),id='old')
            with patch.object(sync,'ROOT',root),patch.object(sync,'DATA_DIR',root/'data'):
                first=sync.assign_task_ids([task('A')],[],dict(todos=[old]),['s','u'])
                result=sync.assign_task_ids([task('B'),task('A')],[],dict(todos=first),['s','u'])
            self.assertEqual(len({item['id'] for item in result}),2)
            self.assertEqual(next(item for item in result if item['moment_id']=='A')['id'],'old')

    def test_only_identical_server_ids_are_deduplicated(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'data').mkdir()
            with patch.object(sync,'ROOT',root),patch.object(sync,'DATA_DIR',root/'data'):
                result=sync.assign_task_ids([task('A'),dict(task('A'),body='Details')],[],{},['s','u'])
            self.assertEqual(len(result),1)
            self.assertEqual(result[0]['body'],'Details')

    def test_already_merged_tasks_do_not_share_ambiguous_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'data').mkdir()
            previous = {'todos': [dict(task('A'), id='merged'), dict(task('B'), id='merged')]}
            with patch.object(sync, 'ROOT', root), patch.object(sync, 'DATA_DIR', root/'data'):
                result = sync.assign_task_ids([task('A'), task('B')], [], previous, ['school','student'])
            self.assertEqual(len({t['id'] for t in result}), 2)
            self.assertTrue(all(t['id'] != 'merged' for t in result))

    def test_all_rejected_records_are_a_failure(self):
        with patch.object(sync,'PlannedElement',side_effect=ValueError('invalid record')):
            with self.assertRaises(ValueError):
                list(sync.parse_planner_records([{}],'planner'))
        self.assertEqual(sync._planner_diagnostics['planner']['skipped'],1)

    def test_private_branches_do_not_become_instructions(self):
        payload={'privateInfo':'secret','wrapper':{'private_info':'also secret'},'linkedPlannedElement':{'description':'linked'}}
        self.assertEqual(planner_details.extract_body(payload,'Task'),'')
        self.assertNotIn('secret',json.dumps(planner_details.public_payload(payload)))

    def test_saved_detail_route_is_rediscovered(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'route.json';path.write_text(json.dumps({'template':'/old/{id}'}))
            fetcher=planner_details.DetailFetcher(Mock(),path,1,'student')
            with patch.object(fetcher,'_get',side_effect=[None,{'publicInfo':'restored'}]),patch.object(planner_details,'CANDIDATE_TEMPLATES',['/new/{id}']):
                self.assertEqual(fetcher.fetch('task','planned-assignments',date(2026,10,15))['publicInfo'],'restored')
            self.assertEqual(fetcher.template,'/new/{id}')

    def test_atomic_snapshot_preserves_old_json_on_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'snapshot.json';path.write_text('{"old":true}')
            with patch.object(sync.os,'replace',side_effect=OSError()):
                with self.assertRaises(OSError):sync.write_snapshot(path,{'new':True})
            self.assertEqual(json.loads(path.read_text()),{'old':True})
