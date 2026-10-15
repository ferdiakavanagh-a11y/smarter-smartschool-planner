from pathlib import Path
import shutil
import subprocess
import unittest

import planner_html


class UiTests(unittest.TestCase):
    def test_javascript_and_failed_saves(self):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node.js is required for release UI checks')
        subprocess.run([node, str(Path(__file__).with_name('state_saves.js'))], check=True, capture_output=True, text=True)
        html = planner_html.render_html({'todos': [], 'days': [], 'all_classes': []}, [], embedded=True)
        script = "const vm=require('node:vm'); let s=''; process.stdin.on('data',d=>s+=d); process.stdin.on('end',()=>{for(const m of s.matchAll(/<script[^>]*>([\\s\\S]*?)<\\/script>/g)) new vm.Script(m[1]);});"
        subprocess.run([node, '-e', script], input=html, check=True, capture_output=True, text=True)
