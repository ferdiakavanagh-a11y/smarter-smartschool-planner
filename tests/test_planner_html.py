import json
import re
import unittest

import planner_html


class PlannerHtmlTests(unittest.TestCase):
    def test_data_placeholders_are_not_replaced_recursively(self):
        tokens = (
            "__WC_VARS__",
            "__EMBEDDED_JSON__",
            "__BOOT_JSON__",
            "__DATA_JSON__",
            "__COMPLETED_JSON__",
            "__SETTINGS_JSON__",
            "__PINNED_JSON__",
            "__NOTES_JSON__",
        )
        marker = " ".join(tokens) + " </script><script>alert(1)</script>"
        data = {
            "generated_at": "2026-01-01T00:00:00",
            "todos": [{"description": marker}],
            "days": [],
            "all_classes": [],
            "results": [],
        }

        html = planner_html.render_html(data, [], embedded=True)

        for token in tokens:
            self.assertIn(token, html)
        payload = re.search(r"var DATA = (.*);", html).group(1)
        self.assertEqual(json.loads(payload), data)
        self.assertNotIn("</script><script>", html)


if __name__ == "__main__":
    unittest.main()
