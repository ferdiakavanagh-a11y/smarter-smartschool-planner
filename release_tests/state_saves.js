const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '..', 'planner_html.py'), 'utf8');
let accepted = false;
let reject = false;
let warnings = 0;
const save = async () => { if (reject) throw Error('disk full'); return accepted; };
const context = vm.createContext({
  EMBEDDED: true, COMPLETED: [], PINNED: [], NOTES: {}, SETTINGS: {}, DATA: {},
  bridge: () => ({mark_task: save, pin_task: save, save_note: save, save_setting: save}),
  render: () => {}, showToast: () => { warnings++; },
});
vm.runInContext(source.slice(source.indexOf('var stateWriteQueue='), source.indexOf('if (!EMBEDDED) {')), context);
(async () => {
  for (reject of [false, true]) {
    assert.equal(await context.markTask('task', true), false);
    assert.equal(await context.togglePin('task'), null);
    assert.equal(await context.saveNote('task', 'draft'), false);
    assert.equal(await context.saveSetting('scheme', 'light'), false);
    assert.equal(context.COMPLETED.length, 0);
    assert.equal(context.PINNED.length, 0);
    assert.equal(context.NOTES.task, undefined);
    assert.equal(context.SETTINGS.scheme, undefined);
  }
  reject = false; accepted = true;
  assert.equal(await context.markTask('task', true), true);
  assert.equal(await context.togglePin('task'), true);
  assert.equal(await context.saveNote('task', 'draft'), true);
  assert.equal(await context.saveSetting('scheme', 'light'), true);
  assert.equal(context.SETTINGS.scheme, 'light');
  assert.equal(context.COMPLETED[0], 'task');
  assert.equal(context.PINNED[0], 'task');
  assert.equal(context.NOTES.task, 'draft');
  await Promise.all([context.togglePin('task'), context.togglePin('task')]);
  assert.equal(context.PINNED[0], 'task');
  assert.equal(warnings, 8);
})().catch(error => { console.error(error); process.exitCode = 1; });
