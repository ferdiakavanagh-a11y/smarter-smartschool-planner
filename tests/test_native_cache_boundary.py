"""Offline cached-data boundary checks; QCoreApplication only, no windows or services."""
import json
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication
import credential_store
import task_state
from qml_app.backend import Backend
from test_qml_migration import snapshot


class CacheBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'data').mkdir()
        self.credentials = dict(main_url='school.example', username='synthetic')
        credentials = patch.object(credential_store, 'load_credentials', return_value=self.credentials)
        credentials.start()
        self.addCleanup(credentials.stop)
        self.data = snapshot(credential_store.account_key(self.credentials))
        self.path = self.root / 'data/planner_data.json'

    def load(self, data):
        self.path.write_text(json.dumps(data), encoding='utf-8')
        backend = Backend(self.root)
        self.addCleanup(backend.shutdown)
        return backend

    def test_nested_record_containers_fail_closed_without_rewriting_cache(self):
        cases = [
            ('days', [{'events': [42]}]),
            ('days', [{'events': None}]),
            ('all_classes', [{'events': [{'info': 'wrong'}]}]),
            ('days', [{'events': [{'info': {'assignments': ['wrong']}}]}]),
            ('lvs', {'notes': None, 'absences': []}),
            ('lvs', {'notes': ['wrong'], 'absences': []}),
            ('lvs', {'notes': [], 'absences': 42}),
            ('optional_section_status', ['wrong']),
            ('results', [{'feedback': 42}]),
        ]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                data = deepcopy(self.data)
                data[key] = value
                backend = self.load(data)
                before = self.path.read_bytes()
                self.assertEqual(backend.data, {})
                self.assertIn('unavailable', backend.status)
                self.assertEqual(backend.unreadCount, 0)
                for section in range(2, 6):
                    self.assertEqual(backend.groups(section, ''), [])
                self.assertEqual(self.path.read_bytes(), before)

    def test_task_link_containers_are_validated_before_detail_display(self):
        for value in (42, 'https://school.example/file', ['wrong']):
            with self.subTest(value=value):
                data = deepcopy(self.data)
                data['todos'][0]['attachments'] = value
                self.assertEqual(self.load(data).data, {})

    def test_valid_and_legacy_optional_shapes_still_load(self):
        data = deepcopy(self.data)
        data['todos'][0]['attachments'] = None
        data['days'][0]['events'][0]['info'] = None
        data['results'][0]['feedback'] = None
        backend = self.load(data)
        self.assertEqual(backend.tasks.rowCount(), 1)
        for section in (2, 4, 5):
            self.assertTrue(backend.groups(section, ''))
        self.assertTrue(backend.taskDetail('task-1'))

    def test_damaged_appearance_values_have_safe_read_only_defaults(self):
        for version in (None, 1):
            with self.subTest(version=version):
                raw = dict(qmlVersion=version, textSize=[], style={}, scheme=[],
                           renderingMode=[], glassLevel='wrong', distortion={}, wallpaperIndex=[],
                           reducedMotion='false', animatedBackground='false', highContrast=1,
                           unrelated={'keep': True})
                path = self.root / 'data/ui_settings.json'
                path.write_text(json.dumps(raw), encoding='utf-8')
                before = path.read_bytes()
                backend = self.load(self.data)
                values = backend.settings
                self.assertEqual(values['textSize'], 1)
                self.assertEqual(values['style'], 'clear')
                self.assertEqual(values['scheme'], 'light')
                self.assertEqual(values['renderingMode'], 'fancy')
                self.assertEqual(values['glassLevel'], 0)
                self.assertEqual(values['distortion'], .5)
                self.assertEqual(values['wallpaperIndex'], 1)
                self.assertIs(values['reducedMotion'], False)
                self.assertIs(values['animatedBackground'], True)
                self.assertIs(values['highContrast'], False)
                self.assertEqual(values['unrelated'], {'keep': True})
                self.assertEqual(path.read_bytes(), before)
                self.assertTrue(backend.saveSettings({key: values[key] for key in
                    ('textSize', 'style', 'scheme', 'renderingMode', 'glassLevel', 'distortion',
                     'wallpaperIndex', 'reducedMotion', 'animatedBackground', 'highContrast')}))
                self.assertEqual(task_state.load_settings(self.root)['unrelated'], {'keep': True})

    def test_malformed_read_state_does_not_break_badges_or_overwrite_it(self):
        backend = self.load(self.data)
        key = backend.read_key()
        for value in (None, 42, 'notes:1', ['notes:1', {}]):
            with self.subTest(value=value):
                task_state.set_setting(self.root, key, value)
                backend._settings = task_state.load_settings(self.root)
                before = (self.root / 'data/ui_settings.json').read_bytes()
                self.assertEqual(backend.unreadCount, 2)
                self.assertTrue(backend.groups(5, '')[0]['items'][0]['unread'])
                self.assertFalse(backend.markRead('*'))
                self.assertEqual((self.root / 'data/ui_settings.json').read_bytes(), before)

    def test_huge_numeric_preferences_are_rejected_without_overflow(self):
        backend = self.load(self.data)
        for value in (10 ** 400, float('nan'), float('inf'), True):
            with self.subTest(value=str(value)[:30]):
                self.assertFalse(backend.saveSettings({'textSize': value}))


if __name__ == '__main__':
    unittest.main()
