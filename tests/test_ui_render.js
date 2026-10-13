// Run with node tests/test_ui_render.js. Tests pure UI functions without a browser.
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const { createHash } = require('node:crypto');
const vm = require('node:vm');
const source = readFileSync(resolve(__dirname, '../planner_html.py'), 'utf8');
const context = vm.createContext({
  DATA: { results: [] }, COMPLETED: [], PINNED: [], NOTES: {}, EMBEDDED: true,
  ICON: new Proxy({}, { get: () => '<svg></svg>' }),
  document: { createElement() {
    let pixels;
    return {
      getContext() { return {
        createImageData(w, h) { return { data: new Uint8ClampedArray(w * h * 4) }; },
        putImageData(image) { pixels = image.data; },
      }; },
      toDataURL() { return pixels; },
    };
  } },
});
vm.runInContext(source.slice(source.indexOf('var activeTab ='), source.indexOf('/* ===== DETAIL SHEET ===== */')), context);
vm.runInContext(source.slice(source.indexOf('function lensMapURL('), source.indexOf('function lensFilterId(')), context);
for (const date of ['2026-01-01', '2026-03-29', '2026-10-25', '2026-12-31', 'not-a-date']) {
  const day = new Date(date + 'T00:00:00');
  assert.equal(context.fmtDate(date), day.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' }));
  assert.equal(context.fmtLong(date), day.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' }));
}
assert.equal(context.fmtDate(null), '-');

// Digests from the original refraction algorithm, including fractional radii.
for (const [size, digest] of [
  [[560, 670, 30, 24], '6a8a2017a0ca080763e6285dcd6de09dfd7cac7740e2f673e9a932f6abb55f82'],
  [[38, 38, 19, 15.2], '1254a69c3392a09acbba5105e5191d0afc3e4bb771d8bea8e0501d0f7207ffa2'],
  [[55, 41, 18, 14.4], '5cbd3e545207ec70f11eb0654ef820e7ef2646c79b6bb7a81d3298939dcbd785'],
  [[17, 29, 8.5, 6.8], 'd591a42e2458773c392bee88fe0a4638c80b8a16fc445d8f130f39abad69dc37'],
]) {
  assert.equal(createHash('sha256').update(context.lensMapURL(...size)).digest('hex'), digest);
}

const names = ["Seán O'Brien-Ó Súilleabháin", 'Đặng Thị Ngọc Hân', '王秀英', 'نور الهدى عبد الرحمن', '👩🏽‍💻 Priya', '<script>alert(1)</script>'];
for (const count of [0, 1, 1000]) {
  const tasks = Array.from({ length: count }, (_, i) => ({
    id: 'task-' + i, course: 'Course ' + i % 8, type: 'Taak',
    description: names[i % names.length], body: 'Read the assignment instructions. '.repeat(70),
    due_date: context.isoOffset(1), posted_date: context.isoOffset(-1),
    attachments: [], weblinks: [],
  }));
  const day = { date: context.isoOffset(0), events: tasks.map(t => ({
    moment_id: t.id, course: t.course, start: '09:00', end: '10:00',
    teacher: null, classroom: null, groups: null, note: '', info: { assignments: [t] },
  })) };
  const data = { todos: tasks, days: count ? [day] : [], all_classes: count ? [day] : [], results: tasks.map(t => ({
    id: t.id, name: t.description, course: t.course, score: 0, max: 10, percent: 0,
    counts: true, feedback: [], date: t.due_date,
  })) };
  context.DATA = data;
  for (const fn of ['renderTodo', 'renderMissed', 'renderSchedule', 'renderAll', 'renderGrades']) {
    const html = context[fn](data, []);
    assert.ok(html.length > 0, fn);
    assert.ok(!html.includes('<script>alert(1)</script>'), fn + ' escapes data');
  }
  if (count) {
    context.NOTES[tasks[0].id] = 'Remember the microscope';
    context.searchQuery = 'microscope';
    assert.ok(context.renderTodo(data, []).includes('Remember the microscope'));
    context.searchQuery = 'no-such-assignment';
    assert.ok(context.renderTodo(data, []).includes('No matches'));
    context.searchQuery = '';
    context.PINNED = [tasks[0].id];
    assert.ok(context.renderTodo(data, []).includes('Pinned'));
    assert.ok(context.renderTodo(data, [tasks[0].id]).includes('Completed'));
    context.PINNED = []; context.NOTES = {};
  }
}
let chipWrites = 0;
const chips = { set innerHTML(value) { chipWrites++; this.html = value; } };
context.document.getElementById = () => chips;
const courses = { todos: [{ course: 'Chemistry' }, { course: 'French' }] };
context.activeTab = 'todo'; context.activeCourse = 'All';
for (let i = 0; i < 20; i++) context.renderChips(courses);
assert.equal(chipWrites, 1, 'unchanged chips retain their DOM and scroll position');
context.activeCourse = 'French'; context.renderChips(courses);
assert.equal(chipWrites, 2);
assert.ok(chips.html.includes('aria-pressed="true" data-course="French"'));
context.activeTab = 'grades'; context.renderChips(courses); context.renderChips(courses);
assert.equal(chipWrites, 3, 'clear chips once when leaving To-Do');

const operations = [], observed = new Set(), removed = [];
function control(name) {
  return { name, __r: 19,
    get offsetWidth() { operations.push('read'); return 38; },
    get offsetHeight() { operations.push('read'); return 38; },
    style: new Proxy({}, { set(target, key, value) { operations.push('write'); target[key] = value; return true; } }),
  };
}
let controls = [control('first'), control('second')];
context.LENS = { ok: true, cache: {}, seen: new Set(), q: new Set(), ro: {
  observe(el) { assert.ok(!observed.has(el)); observed.add(el); },
  unobserve(el) { observed.delete(el); removed.push(el); },
} };
context.LENS_SEL = [['.chip', 0.5]];
context.lensFilterId = () => 'same-filter';
context.document.querySelectorAll = () => controls;
vm.runInContext(source.slice(source.indexOf('function lensMeasure('), source.indexOf('var _renderLens')), context);
context.lensScan();
assert.ok(operations.lastIndexOf('read') < operations.indexOf('write'), 'all layout reads precede filter writes');
operations.length = 0;
context.lensScan();
assert.ok(!operations.includes('write'), 'unchanged controls do not rewrite filters');
const detached = controls[0]; context.LENS.q.add(detached);
controls = [controls[1], control('replacement')]; context.lensScan();
assert.equal(removed[0], detached);
assert.equal(observed.size, 2, 'observer registration stays bounded across redraws');
assert.ok(!context.LENS.q.has(detached));
const releasedFilters = [];
context.document.getElementById = id => ({ remove() { releasedFilters.push(id); } });
context.LENS.cache.active = 'same-filter';
for (let i = 0; i < 64; i++) context.LENS.cache['unused-' + i] = 'filter-' + i;
context.lensPrune();
assert.equal(Object.keys(context.LENS.cache).length, 32);
assert.equal(context.LENS.cache.active, 'same-filter', 'visible controls keep their exact refraction filter');
assert.equal(releasedFilters.length, 33, 'unused SVG filters are released along with cache entries');
assert.ok(!releasedFilters.includes('same-filter'));
let sheetLayouts = 0;
context.sheetAnim = 0; context.cancelAnimationFrame = () => {};
context.sheetEl = { style: {}, get offsetHeight() { sheetLayouts++; return 400; } };
context.scrimEl = { style: {} };
vm.runInContext(source.slice(source.indexOf('function sheetResetStyles('), source.indexOf('function restoreFocus(')), context);
context.sheetResetStyles();
assert.equal(sheetLayouts, 0, 'normal menu open avoids a forced layout reset');
context.sheetEl.style.transform = 'translate(0,100px)'; context.scrimEl.style.opacity = '0.7';
context.sheetResetStyles();
assert.equal(sheetLayouts, 1, 'interrupted gestures retain the transition reset');
assert.equal(context.sheetEl.style.transform, ''); assert.equal(context.scrimEl.style.opacity, '');
function classList(initial = []) {
  const values = new Set(initial);
  return { contains: name => values.has(name), add: name => values.add(name), remove: name => values.delete(name),
    toggle(name, on) { if (on === undefined) on = !values.has(name); if (on) values.add(name); else values.delete(name); return on; } };
}
const settings = {}, menuEvents = [];
const input = () => ({ value: '1', listeners: {}, classList: classList(), setAttribute() {},
  addEventListener(name, fn) { (this.listeners[name] ||= []).push(fn); } });
const slider = input(), motion = input(), background = input();
const targets = { glassSlider: slider, motionToggle: motion, bgToggle: background, sheetTitle: { textContent: '' },
  sheetBody: { scrollTop: 0, set innerHTML(value) {
    menuEvents.push('build'); this.html = value;
    for (const el of [slider, motion, background]) el.listeners = {};
  } } };
context.sheetEl.classList = classList(); context.sheetEl.focus = () => menuEvents.push('focus');
context.scrimEl.classList = classList(); context.document.body = { classList: classList() };
context.document.documentElement = { getAttribute: () => 'vivid' };
context.document.getElementById = id => targets[id];
context.document.querySelectorAll = () => [motion, background];
context.loadSetting = key => settings[key] ?? null;
context.saveSetting = (key, value) => settings[key] = value;
context.applyGlassLevel = () => {};
context.setInert = () => {};
context.lensApplyBatch = () => {
  assert.ok(!context.sheetEl.classList.contains('show'), 'filter preparation precedes entrance');
  menuEvents.push('filter');
};
vm.runInContext(source.slice(source.indexOf('function showSheet('), source.indexOf('function hideSheet(')), context);
vm.runInContext(source.slice(source.indexOf('function currentLevel('), source.indexOf('function applyScheme(')), context);
for (let i = 0; i < 25; i++) { context.sheetEl.classList.remove('show'); context.openSettings(); }
assert.equal(menuEvents.filter(x => x === 'build').length, 1, 'unchanged settings reuse controls');
assert.equal(menuEvents.filter(x => x === 'filter').length, 1, 'warm settings reuse their prepared filter');
assert.equal(menuEvents.filter(x => x === 'focus').length, 25, 'every opening restores menu focus');
assert.equal(motion.listeners.click.length, 1, 'reopening must not duplicate toggle handlers');
assert.equal(slider.listeners.input.length, 1);
slider.value = '2'; slider.listeners.input[0]();
context.sheetEl.classList.remove('show'); context.openSettings();
assert.equal(menuEvents.filter(x => x === 'build').length, 2, 'changed settings update the controls');
assert.ok(targets.sheetBody.html.includes('value="2"'));
context.sheetEl.classList.remove('show'); context.showSheet('Task', 'task body');
context.sheetEl.classList.remove('show'); context.openSettings();
assert.equal(menuEvents.filter(x => x === 'build').length, 4, 'returning from details restores settings');
console.log('PASS: renderer/state parity; chip/filter lifecycle; sheet gestures; settings reuse, invalidation, focus and event handlers');
