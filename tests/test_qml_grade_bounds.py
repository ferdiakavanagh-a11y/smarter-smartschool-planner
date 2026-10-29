"""Synthetic grade overflow regressions; no UI, network, credentials or saved data."""
import unittest
from types import SimpleNamespace

from qml_app.sections import finite, grade_presentation, groups


class GradeBoundsTests(unittest.TestCase):
    def test_finite_inputs_with_overflowing_percent_keep_score(self):
        presentation, numeric = grade_presentation(dict(score=1e308, max=1))
        self.assertTrue(numeric)
        self.assertEqual(presentation['percentText'], '')
        self.assertNotIn('inf', presentation['extra'])
        self.assertFalse(finite(10**1000))

    def test_overflowing_totals_keep_the_correct_weighted_average(self):
        backend = SimpleNamespace(data=dict(results=[
            dict(id=str(i), course='Synthetic course', score=1e308, max=1e308, counts=True)
            for i in range(2)
        ]))
        result = groups(backend, 4, '')
        self.assertEqual(result[0]['items'][0]['title'], '100%')
        self.assertEqual(result[1]['average'], '100%')
        self.assertNotIn('inf', result[0]['items'][0]['body'])

    def test_normal_grade_thresholds_are_unchanged(self):
        backend = SimpleNamespace(data=dict(results=[
            dict(id='a', course='Math', score=8, max=10, counts=True),
            dict(id='b', course='Math', score=20, max=30, counts=True),
        ]))
        result = groups(backend, 4, '')
        self.assertEqual(result[0]['items'][0]['title'], '70%')
        self.assertEqual(result[0]['items'][0]['tone'], 'green')


if __name__ == '__main__':
    unittest.main()
