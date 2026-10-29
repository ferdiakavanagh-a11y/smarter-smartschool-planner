import base64
from datetime import date
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import dutch_dates
import gemini_dates as ai
import updater


class DatesUpdatesTests(unittest.TestCase):
    def setUp(self):
        # These monitor tests execute harmless stub programs, not release binaries.
        signature = patch.object(updater, 'verify_installer_signature')
        signature.start()
        self.addCleanup(signature.stop)

    def test_next_week_weekdays(self):
        for text in ('Tegen volgende week vrijdag afwerken', 'Tegen vrijdag volgende week afwerken'):
            self.assertEqual(dutch_dates.extract_due_date(text, date(2026, 10, 15))[0], date(2026, 10, 23))
        self.assertEqual(dutch_dates.extract_due_date('Tegen vrijdag afwerken', date(2026, 10, 15))[0], date(2026, 10, 16))

    def test_invalid_ai_shapes_are_rejected(self):
        for answer in ('{}', '{"error":"oops"}', '[{}]', '[{"id":0,"due_date":null,"confidence":"maybe"}]', '[{"id":0.5,"due_date":null,"confidence":"high"}]'):
            self.assertIsNone(ai._parse_response(answer))

    def test_uncertain_answers_remain_retryable(self):
        item = ('Afwerken tegen volgende vrijdag', date(2026, 10, 15))
        for due, confidence, cached in [('2026-10-16', 'low', False), ('bad', 'high', False), ('2026-10-16invalid', 'high', False), ('', 'high', False), (None, 'high', True)]:
            with self.subTest(due=due, confidence=confidence), tempfile.TemporaryDirectory() as folder:
                path = Path(folder)/'cache.json'
                response = SimpleNamespace(text=json.dumps([dict(id=0,due_date=due,confidence=confidence)]))
                with patch.object(ai, '_get_client'), patch.object(ai, '_generate', return_value=(response,'test')):
                    ai.extract_due_dates_batch([item], 'fake', path)
                self.assertEqual(ai._cache_key(*item) in json.loads(path.read_text()), cached)

    def test_unexpected_ai_answer_is_not_cached(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'cache.json'
            with patch.object(ai,'_get_client'), patch.object(ai,'_generate',return_value=(SimpleNamespace(text='{}'),'test')):
                ai.extract_due_dates_batch([('Afwerken tegen vrijdag',date(2026,10,15))],'fake',path)
            self.assertEqual(ai.last_problem['kind'],'format')
            self.assertFalse(path.exists())

    def test_invalid_existing_cache_is_retried(self):
        item=('Afwerken tegen vrijdag',date(2026,10,15))
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'cache.json'
            path.write_text(json.dumps({ai._cache_key(*item):'invalid'}))
            response=SimpleNamespace(text='[{"id":0,"due_date":"2026-10-16","confidence":"high"}]')
            with patch.object(ai,'_get_client'), patch.object(ai,'_generate',return_value=(response,'test')) as generate:
                dates,_=ai.extract_due_dates_batch([item],'fake',path)
            generate.assert_called_once()
            self.assertEqual(dates,[date(2026,10,16)])

    def test_ai_request_timeout_respects_remaining_budget(self):
        client = Mock()
        with patch.object(ai.time,'monotonic',side_effect=[0,0,0,3]):
            ai._generate(client,'task',Mock(),time_budget=5)
        config = client.models.generate_content.call_args.kwargs['config']
        self.assertEqual(config['http_options']['timeout'],2000)
        self.assertEqual(config['http_options']['retry_options']['attempts'],1)

    def test_shared_budget_stops_later_batches(self):
        items=[(f'Tegen vrijdag taak {i}',date(2026,10,15)) for i in range(2)]
        response=SimpleNamespace(text='[{"id":0,"due_date":null,"confidence":"high"}]')
        with patch.object(ai,'_get_client'), patch.object(ai,'MAX_ITEMS_PER_REQUEST',1), patch.object(ai.time,'monotonic',side_effect=[0,1,100]), patch.object(ai,'_generate',return_value=(response,'test')) as generate:
            ai.extract_due_dates_batch(items,'fake')
        generate.assert_called_once()
        self.assertEqual(ai.last_problem['kind'],'unavailable')

    def test_installer_worker_observes_exit_and_reopens_on_failure(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(updater.subprocess,'Popen') as popen:
            root=Path(folder)
            status=root/'data'/'install_result.json'
            popen.side_effect=lambda *args, **kwargs: status.write_text('{"status":"running"}')
            updater.launch_installer(root/"installer's.exe",root)
            args=popen.call_args.args[0]
            options=popen.call_args.kwargs
            self.assertTrue(options['creationflags'] & updater.subprocess.CREATE_NO_WINDOW)
            self.assertFalse(options['creationflags'] & updater.subprocess.DETACHED_PROCESS)
            self.assertEqual(options['stdin'],updater.subprocess.DEVNULL)
            self.assertEqual(options['stderr'],updater.subprocess.STDOUT)
            script=base64.b64decode(args[-1]).decode('utf-16-le')
            self.assertIn('-PassThru -Wait',script)
            self.assertIn('installer\'\'s.exe',script)
            self.assertIn('if ($code -ne 0)',script)
            self.assertIn('--update-failed',script)
            self.assertEqual(args[-3:-1],['Hidden','-EncodedCommand'])
            status.write_text('{"status":"failed","code":5}')
            self.assertTrue(updater.pending_install_failure(root))
            updater.acknowledge_install_failure(root)
            self.assertFalse(updater.pending_install_failure(root))

    def test_failed_worker_start_keeps_the_app_open(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(updater.subprocess, 'Popen', return_value=Mock(poll=lambda: 1)):
            with self.assertRaises(updater.UpdateError):
                updater.launch_installer(Path(folder)/'fake.exe',Path(folder))

    @unittest.skipUnless(os.name == 'nt', 'Windows PowerShell monitor')
    def test_real_monitor_reports_stub_installer_exit(self):
        # Harmless batch files exercise the worker without installing or closing anything.
        for code in (0, 7):
            with self.subTest(code=code), tempfile.TemporaryDirectory(prefix="monitor's space ") as folder:
                root=Path(folder)
                installer=root/'stub.cmd'
                installer.write_text(f'@exit /b {code}\n')
                workers=[]
                real_popen=updater.subprocess.Popen
                def spawn(*args, **kwargs):
                    worker=real_popen(*args, **kwargs)
                    workers.append(worker)
                    return worker
                with patch.object(updater.subprocess,'Popen',side_effect=spawn):
                    updater.launch_installer(installer,root)
                result=root/'data'/'install_result.json'
                deadline=time.monotonic()+15
                while time.monotonic()<deadline:
                    status=json.loads(result.read_text(encoding='utf-8-sig'))
                    if status['status']!='running':
                        break
                    time.sleep(0.1)
                self.assertEqual(status,{'status':'ok' if code==0 else 'failed','code':code})
                # The failure branch tries to reopen the absent app; let it finish before cleanup.
                workers[0].wait(timeout=15)
