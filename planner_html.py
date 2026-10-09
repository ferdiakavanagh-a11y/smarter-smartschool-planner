"""Shared HTML/CSS/JS for the planner UI, used by build_dashboard.py (read-only) and desktop_app.py (interactive).

render_html(data, completed_ids, embedded, settings) builds the page; embedded=True uses pywebview's
bridge, False works locally in a browser. The UI lives in TEMPLATE."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

TEMPLATE = r'''<!DOCTYPE html>
<html lang="en" data-style="vivid">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Planner</title>
<style>
:root{color-scheme:dark light;
--blue:#0A84FF;--orange:#FF9F0A;--purple:#BF5AF2;--red:#FF453A;--green:#30D158;--yellow:#FFD60A;--teal:#64D2FF;--pink:#FF375F;
--glass-opacity:.55;--glass-blur:26px;--glass-saturate:170%;--glass-specular:.9;
--glass-tint:255,255,255;--glass-tint-dark:18,18,28;
--gloss:255,255,255;--gloss-border:.25;--gloss-hi:.35;--gloss-hi-sm:.25;
--glass-inner:rgba(0,0,0,.25);--glass-drop:rgba(0,0,0,.45);--glass-drop-sm:rgba(0,0,0,.35);
--bg:#000;--bg-elev:#1c1c1e;--separator:rgba(255,255,255,.08);--separator-strong:rgba(255,255,255,.18);
--text:#fff;--text-secondary:rgba(235,235,245,.6);--text-tertiary:rgba(235,235,245,.3);--fill:rgba(120,120,128,.32);
--radius-card:24px;--radius-row:18px;--radius-chip:999px;--radius-sheet:30px;
--ease-spring:cubic-bezier(.34,1.56,.64,1);--ease-out:cubic-bezier(.22,1,.36,1);--dur:300ms;--tab-count:5;
--font:"SF Pro Display","SF Pro Text","Segoe UI Variable","Segoe UI",system-ui,-apple-system,sans-serif;
}
@media (prefers-color-scheme:light){:root{
--blue:#007AFF;--orange:#FF9500;--purple:#AF52DE;--red:#FF3B30;--green:#34C759;--yellow:#FFCC00;--teal:#5AC8FA;--pink:#FF2D55;
--bg:#f2f2f7;--bg-elev:#fff;--separator:rgba(60,60,67,.12);--separator-strong:rgba(60,60,67,.24);
--text:#000;--text-secondary:rgba(60,60,67,.6);--text-tertiary:rgba(60,60,67,.3);--fill:rgba(120,120,128,.16);
--glass-tint:255,255,255;--glass-tint-dark:255,255,255;
--gloss-border:.7;--gloss-hi:.9;--gloss-hi-sm:.7;--glass-inner:rgba(0,0,0,.06);--glass-drop:rgba(0,0,0,.18);--glass-drop-sm:rgba(0,0,0,.12);
}}

/* FROSTED: */
[data-style="frost"]{
--blue:#4A82B0;--orange:#C2A06B;--purple:#9C92BC;--red:#D98C8C;--green:#8FB89A;--teal:#7FA8C0;--pink:#B0B8C4;--yellow:#D8C896;
--bg:#10161E;--bg-elev:#1A2230;--text:#F2F5FA;--text-secondary:rgba(220,228,240,.62);--text-tertiary:rgba(220,228,240,.34);
--separator:rgba(255,255,255,.07);--separator-strong:rgba(255,255,255,.14);--fill:rgba(120,140,170,.26);
--gloss:255,255,255;--gloss-border:.4;--gloss-hi:.55;--gloss-hi-sm:.4;
--glass-inner:rgba(40,52,68,.18);--glass-drop:rgba(28,40,56,.34);--glass-drop-sm:rgba(28,40,56,.24);
}
@media (prefers-color-scheme:light){[data-style="frost"]{
--blue:#3A6A98;--orange:#9A6E2E;--purple:#5E5490;--red:#A84545;--green:#3F805A;--teal:#2E7A92;--pink:#8088A0;--yellow:#9A8628;
--bg:#E9EFF5;--bg-elev:#fff;--text:#0A1420;--text-secondary:rgba(40,60,84,.66);--text-tertiary:rgba(40,60,84,.4);
--separator:rgba(60,84,110,.12);--separator-strong:rgba(60,84,110,.22);--fill:rgba(60,84,110,.14);
--gloss-border:.85;--gloss-hi:.95;--gloss-hi-sm:.8;--glass-inner:rgba(60,82,108,.08);--glass-drop:rgba(40,62,86,.14);--glass-drop-sm:rgba(40,62,86,.10);
}}
[data-style="frost"] #wallpaper{opacity:.4}
[data-style="frost"] .blob{animation-duration:44s}
[data-style="frost"] .group::before,[data-style="frost"] #tabbar::before,[data-style="frost"] #sheet::before,[data-style="frost"] #header::before{
content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;opacity:.05;z-index:0;
background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='140' height='140'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
}

*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%}
body{font-family:var(--font);background:var(--bg);color:var(--text);overflow:hidden;position:fixed;inset:0;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;font-variant-numeric:tabular-nums}
button{font-family:inherit;color:inherit;background:none;border:none;cursor:pointer}
button:focus-visible,input:focus-visible,textarea:focus-visible,summary:focus-visible{outline:2px solid var(--blue);outline-offset:2px}
::selection{background:color-mix(in srgb,var(--blue) 30%,transparent)}

#wallpaper{position:fixed;inset:-10%;z-index:0;opacity:.9;pointer-events:none;transition:opacity 500ms var(--ease-out)}
body.page-hidden #wallpaper{visibility:hidden}
body.sheet-open .blob{animation-play-state:paused}
.blob{position:absolute;border-radius:50%;animation:drift 26s ease-in-out infinite alternate}
.b1{width:55vw;height:55vw;left:-10vw;top:-10vh;background:radial-gradient(closest-side,var(--blue),color-mix(in srgb,var(--blue) 50%,transparent) 35%,color-mix(in srgb,var(--blue) 16%,transparent) 68%,transparent)}
.b2{width:50vw;height:50vw;right:-8vw;top:5vh;background:radial-gradient(closest-side,var(--purple),color-mix(in srgb,var(--purple) 50%,transparent) 35%,color-mix(in srgb,var(--purple) 16%,transparent) 68%,transparent);animation-delay:-6s}
.b3{width:48vw;height:48vw;left:20vw;bottom:-12vh;background:radial-gradient(closest-side,var(--teal),color-mix(in srgb,var(--teal) 50%,transparent) 35%,color-mix(in srgb,var(--teal) 16%,transparent) 68%,transparent);animation-delay:-12s}
.b4{width:40vw;height:40vw;right:10vw;bottom:-8vh;background:radial-gradient(closest-side,var(--orange),color-mix(in srgb,var(--orange) 50%,transparent) 35%,color-mix(in srgb,var(--orange) 16%,transparent) 68%,transparent);animation-delay:-18s}
.b5{width:34vw;height:34vw;left:38vw;top:30vh;background:radial-gradient(closest-side,var(--pink),color-mix(in srgb,var(--pink) 50%,transparent) 35%,color-mix(in srgb,var(--pink) 16%,transparent) 68%,transparent);animation-delay:-9s}
@keyframes drift{0%{transform:translate(0,0) scale(1)}50%{transform:translate(4vw,-3vh) scale(1.12)}100%{transform:translate(-3vw,4vh) scale(.95)}}

#app{position:relative;z-index:1;height:100%;display:flex;flex-direction:column;transition:opacity 220ms var(--ease-out)}

.glass{
background:rgba(var(--glass-tint-dark),var(--glass-opacity));
-webkit-backdrop-filter:blur(var(--glass-blur)) saturate(var(--glass-saturate));backdrop-filter:blur(var(--glass-blur)) saturate(var(--glass-saturate));
border:.5px solid rgba(var(--gloss),calc(var(--gloss-border) * var(--glass-specular)));
box-shadow:inset 0 1px 1px rgba(var(--gloss),calc(var(--gloss-hi) * var(--glass-specular))),inset 0 -1px 2px var(--glass-inner),0 12px 40px var(--glass-drop);
transition:background-color 260ms var(--ease-out),box-shadow 260ms var(--ease-out),border-color 260ms var(--ease-out);
}

#header{position:relative;z-index:5;padding:14px 20px 10px;transition:background var(--dur) var(--ease-out)}
#header.scrolled{background:rgba(var(--glass-tint-dark),calc(var(--glass-opacity) + .2));-webkit-backdrop-filter:blur(var(--glass-blur)) saturate(var(--glass-saturate));backdrop-filter:blur(var(--glass-blur)) saturate(var(--glass-saturate));border-bottom:.5px solid var(--separator)}
.header-top{display:flex;align-items:center;justify-content:space-between;gap:12px;position:relative;z-index:1}
.header-title-wrap{display:flex;flex-direction:column;min-width:0}
.header-title{font-size:34px;font-weight:700;letter-spacing:-.022em;line-height:1.1;transition:font-size var(--dur) var(--ease-out);white-space:nowrap}
#header.scrolled .header-title{font-size:20px}
.header-subtitle{font-size:13px;color:var(--text-secondary);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.header-actions{display:flex;gap:8px;flex-shrink:0}
.icon-btn{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;transition:transform 120ms var(--ease-out)}
.icon-btn:active{transform:scale(.88)}
.icon-btn svg{width:20px;height:20px}
.sync-spin{animation:spin .9s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

#scroll{flex:1;overflow-y:auto;overflow-x:hidden;padding:6px 16px 120px;scroll-behavior:smooth}
#scroll::-webkit-scrollbar{width:8px}
#scroll::-webkit-scrollbar-thumb{background:var(--fill);border-radius:8px}
#scroll::-webkit-scrollbar-track{background:transparent}

#chips{display:flex;gap:8px;overflow-x:auto;padding:4px 20px 12px;scrollbar-width:none}
#chips:empty{display:none}
#chips::-webkit-scrollbar{display:none}
.chip{flex-shrink:0;padding:7px 15px;border-radius:var(--radius-chip);font-size:14px;font-weight:500;color:var(--text);background:rgba(var(--glass-tint-dark),.4);border:.5px solid rgba(255,255,255,.12);transition:transform 120ms var(--ease-out),background 200ms,color 200ms;white-space:nowrap}
.chip:active{transform:scale(.94)}
.chip.active{background:var(--blue);color:#fff;border-color:transparent}

.section{margin-bottom:26px}
.section-header{font-size:22px;font-weight:700;letter-spacing:-.02em;padding:6px 8px 10px;display:flex;align-items:baseline;justify-content:space-between}
.section-header .count{font-size:14px;font-weight:500;color:var(--text-secondary)}
.group{position:relative;border-radius:var(--radius-card);overflow:hidden;
background:rgba(var(--glass-tint-dark),calc(var(--glass-opacity) * .7));
-webkit-backdrop-filter:blur(var(--glass-blur)) saturate(var(--glass-saturate));backdrop-filter:blur(var(--glass-blur)) saturate(var(--glass-saturate));
border:.5px solid rgba(var(--gloss),calc(var(--gloss-border) * .8 * var(--glass-specular)));
box-shadow:inset 0 1px 1px rgba(var(--gloss),calc(var(--gloss-hi-sm) * var(--glass-specular))),0 8px 30px var(--glass-drop-sm);
transition:background-color 260ms var(--ease-out),box-shadow 260ms var(--ease-out)}

.task-row{display:flex;align-items:flex-start;gap:14px;padding:14px 16px;position:relative;transition:opacity 200ms,background 200ms;cursor:pointer}
.task-row+.task-row::before{content:"";position:absolute;left:58px;right:0;top:0;height:.5px;background:var(--separator)}
.task-row:active,.lesson-row:active{background:rgba(255,255,255,.06)}
.task-row.done{opacity:.45}
.task-row.done .task-desc{text-decoration:line-through}
.task-row.done.overdue,.task-row.done.warning{background:none}
.task-row.leaving{opacity:0;transform:translateX(12px);pointer-events:none;transition:opacity 220ms,transform 220ms var(--ease-out)}
.completed-toggle{width:100%;display:flex;align-items:center;justify-content:space-between;padding:6px 8px 10px;font-size:22px;font-weight:700;letter-spacing:-.02em;text-align:left}
.completed-toggle .meta{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:500;color:var(--text-secondary)}
.completed-toggle svg{width:16px;height:16px;transition:transform 260ms var(--ease-spring)}
.completed-toggle.open svg{transform:rotate(90deg)}
.empty.compact{padding:36px 30px 28px}
.task-row.overdue{background:linear-gradient(90deg,color-mix(in srgb,var(--red) 10%,transparent),transparent 60%)}
.task-row.warning{background:linear-gradient(90deg,color-mix(in srgb,var(--orange) 12%,transparent),transparent 60%)}
.check{width:26px;height:26px;border-radius:50%;border:2px solid var(--text-tertiary);flex-shrink:0;margin-top:1px;display:grid;place-items:center;transition:border-color 200ms,background 200ms,transform 120ms;position:relative}
.check::before{content:"";position:absolute;inset:-9px}
.check:active{transform:scale(.85)}
.check.done{border-color:var(--blue);background:var(--blue)}
.check.done::after{content:"";width:12px;height:7px;border-left:2px solid #fff;border-bottom:2px solid #fff;transform:rotate(-45deg) translate(1px,-1px)}
.check.warn-ring{border-color:var(--red)}
.task-body{min-width:0;flex:1}
.task-line1{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.task-course{font-size:15px;font-weight:600}
.task-desc{font-size:15px;line-height:1.35;margin-top:2px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.task-info{font-size:13px;letter-spacing:.005em;line-height:1.35;color:var(--text-secondary);margin-top:4px;display:-webkit-box;-webkit-line-clamp:2;line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;white-space:pre-line}
.detail-info{font-size:16px;line-height:1.45;white-space:pre-wrap;padding:14px;border-radius:var(--radius-row);background:color-mix(in srgb,var(--text) 5%,transparent)}
.today-tag{font-size:12px;font-weight:600;padding:2px 8px;border-radius:999px;margin-left:8px;vertical-align:middle;background:color-mix(in srgb,var(--blue) 22%,transparent);color:var(--blue)}
.task-row .task-body{padding-right:26px}
.task-pin{position:absolute;top:10px;right:10px;width:30px;height:30px;border-radius:50%;display:grid;place-items:center;color:var(--text-tertiary);opacity:0;transition:opacity 150ms,color 150ms,transform 120ms}
.task-pin::before{content:"";position:absolute;inset:-7px}
.task-pin svg{width:16px;height:16px}
.task-row:hover .task-pin,.task-pin.on{opacity:1}
.task-pin.on{color:var(--orange)}
.task-pin.on svg{fill:currentColor}
.task-pin:active{transform:scale(.85)}
.task-note{font-size:13px;line-height:1.35;color:var(--orange);margin-top:4px;font-style:italic;display:-webkit-box;-webkit-line-clamp:1;line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}
.task-meta svg.mini{width:13px;height:13px;vertical-align:-2px;margin-right:2px}
#searchbar{display:none;padding:2px 20px 10px;position:relative;z-index:4}
body.searching #searchbar{display:block}
#searchInput{width:100%;box-sizing:border-box;border:0;outline:none;border-radius:999px;padding:11px 42px 11px 18px;font:inherit;font-size:15px;color:var(--text);background:var(--fill)}
#searchInput::placeholder{color:var(--text-secondary)}
#searchClear{position:absolute;right:30px;top:50%;transform:translateY(-62%);width:26px;height:26px;border-radius:50%;display:grid;place-items:center;color:var(--text-secondary)}
.overview{padding:16px 18px 14px}
.overview .summary-text{font-size:15px;line-height:1.45;white-space:pre-line}
.busy{display:flex;gap:8px;align-items:flex-end;height:92px;margin-top:14px}
.busy-col{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:4px;height:100%}
.busy-bar{width:100%;max-width:36px;border-radius:9px 9px 4px 4px;background:var(--blue);min-height:4px;transition:height 300ms var(--ease-out)}
.busy-col.mid .busy-bar{background:var(--orange)}
.busy-col.high .busy-bar{background:var(--red)}
.busy-col.zero .busy-bar{background:var(--fill)}
.busy-n{font-size:12px;font-weight:600;color:var(--text)}
.busy-col.zero .busy-n{color:var(--text-secondary)}
.busy-day{font-size:11px;color:var(--text-secondary)}
.busy-col.today .busy-day{font-weight:700;color:var(--text)}
.busy-legend{font-size:12px;color:var(--text-secondary);margin-top:8px}
.chip-link{display:inline-flex;align-items:center;gap:6px;max-width:100%;padding:8px 13px;border-radius:999px;background:var(--fill);font-size:14px;margin:0 8px 8px 0;cursor:pointer;word-break:break-word}
.chip-link.static{cursor:default}
.chip-link svg{width:15px;height:15px;flex-shrink:0}
.note-area{width:100%;box-sizing:border-box;min-height:110px;resize:vertical;border:0;outline:none;border-radius:var(--radius-row);padding:12px 14px;font:inherit;font-size:15px;line-height:1.4;color:var(--text);background:color-mix(in srgb,var(--text) 6%,transparent)}
.btn-secondary{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:13px;border-radius:var(--radius-row);font-size:15px;font-weight:600;background:var(--fill);color:var(--text);margin-bottom:10px}
.btn-secondary svg{width:16px;height:16px}
.grade-row{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:13px 16px;position:relative;cursor:pointer}
.grade-row+.grade-row::before{content:"";position:absolute;left:16px;right:0;top:0;height:.5px;background:var(--separator)}
.grade-name{font-weight:500;font-size:15px}
.grade-meta{font-size:13px;color:var(--text-secondary);margin-top:2px}
.grade-score{font-size:17px;font-weight:700;text-align:right;white-space:nowrap}
.grade-pct{font-size:12px;color:var(--text-secondary);font-weight:500;text-align:right}
.grade-square{display:inline-block;width:26px;height:26px;border-radius:8px;vertical-align:middle;box-shadow:inset 0 0 0 1px rgba(255,255,255,.4),0 1px 4px rgba(0,0,0,.22)}
.avg-pill{display:inline-block;margin-left:8px;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:700;vertical-align:middle;background:var(--fill)}
.grade-summary{padding:16px 18px;display:flex;align-items:baseline;justify-content:space-between;gap:12px}
.grade-summary b{font-size:28px;letter-spacing:-.02em}
.task-meta{font-size:13px;color:var(--text-secondary);margin-top:6px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}

.badge{display:inline-flex;align-items:center;gap:4px;font-size:12px;font-weight:600;padding:3px 8px;border-radius:999px;letter-spacing:.02em}
.badge svg{width:13px;height:13px}
.badge-type{background:var(--fill);color:var(--text)}
.badge-type.toets{background:color-mix(in srgb,var(--red) 22%,transparent);color:var(--red)}
.badge-type.taak{background:color-mix(in srgb,var(--blue) 22%,transparent);color:var(--blue)}
.badge-type.opdracht{background:color-mix(in srgb,var(--purple) 22%,transparent);color:var(--purple)}
.badge-corrected{background:color-mix(in srgb,var(--orange) 20%,transparent);color:var(--orange)}
.badge-ai{background:color-mix(in srgb,var(--purple) 20%,transparent);color:var(--purple)}
.badge-warn{background:color-mix(in srgb,var(--red) 20%,transparent);color:var(--red)}

.lesson-row{display:flex;gap:12px;padding:14px 16px;position:relative;cursor:pointer;transition:background 200ms}
.lesson-row+.lesson-row::before{content:"";position:absolute;left:78px;right:0;top:0;height:.5px;background:var(--separator)}
.lesson-time{flex-shrink:0;width:62px;font-size:13px;font-weight:600;color:var(--text-secondary);padding-top:2px}
.lesson-time .end{display:block;color:var(--text-secondary);font-weight:500;font-size:12px}
.lesson-bar{width:4px;border-radius:4px;flex-shrink:0;align-self:stretch;background:var(--blue)}
.lesson-bar.frans{background:var(--purple)}.lesson-bar.geschiedenis{background:var(--orange)}.lesson-bar.nederlands{background:var(--green)}
.lesson-bar.english,.lesson-bar.engels{background:var(--teal)}
.lesson-body{min-width:0;flex:1}
.lesson-title{font-size:15px;font-weight:600}
.lesson-sub{font-size:13px;letter-spacing:.005em;color:var(--text-secondary);margin-top:2px}
.lesson-assign{margin-top:8px;padding:8px 10px;border-radius:12px;background:color-mix(in srgb,var(--blue) 12%,transparent);font-size:13px;display:flex;gap:8px;align-items:flex-start}
.lesson-assign .check{width:20px;height:20px;margin-top:0;border-width:1.5px}
.lesson-assign .check.done::after{width:9px;height:5px}
.lesson-assign .check.done{border-width:0}

.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 30px;text-align:center;gap:14px}
.empty svg{width:64px;height:64px;opacity:.5;color:var(--text-secondary)}
.empty h3{font-size:20px;font-weight:700}
.empty p{font-size:15px;color:var(--text-secondary);max-width:280px;line-height:1.4}

#tabbar{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);z-index:20;display:flex;border-radius:var(--radius-chip);padding:8px;gap:0;width:min(560px,calc(100% - 32px));justify-content:space-around}
#tabbar .bubble{position:absolute;top:8px;bottom:8px;left:8px;width:calc((100% - 16px) / var(--tab-count));border-radius:var(--radius-chip);background:rgba(255,255,255,.14);border:.5px solid rgba(255,255,255,.2);transition:transform 360ms cubic-bezier(.3,1.2,.5,1);z-index:0;box-shadow:inset 0 1px 1px rgba(255,255,255,.25)}
@media (prefers-color-scheme:light){#tabbar .bubble{background:rgba(255,255,255,.55);box-shadow:inset 0 1px 1px rgba(255,255,255,.8)}}
.tab{position:relative;z-index:1;flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;padding:8px 4px;border-radius:var(--radius-chip);font-size:11px;font-weight:500;letter-spacing:.02em;color:var(--text-secondary);transition:color 200ms,transform 120ms;min-width:0}
.tab:active{transform:scale(.92)}
.tab.active{color:var(--text)}
.tab svg{width:24px;height:24px}
.tab-badge{position:absolute;top:2px;right:calc(50% - 22px);min-width:17px;height:17px;padding:0 5px;border-radius:999px;background:var(--red);color:#fff;font-size:11px;font-weight:700;display:grid;place-items:center;border:2px solid var(--bg)}

#sheet-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:30;opacity:0;pointer-events:none;transition:opacity 280ms var(--ease-out)}
#sheet-backdrop.show{opacity:1;pointer-events:auto}
#sheet{position:fixed;left:50%;bottom:0;transform:translate(-50%,100%);width:min(560px,100%);max-height:86vh;z-index:31;border-radius:var(--radius-sheet) var(--radius-sheet) 0 0;padding:0 0 24px;overflow:hidden;transition:transform 300ms var(--ease-out);display:flex;flex-direction:column}
#sheet.show{transform:translate(-50%,0);transition-duration:420ms}
.sheet-grabber{width:40px;height:5px;border-radius:3px;background:var(--text-tertiary);margin:9px auto 6px;flex-shrink:0}
.sheet-head{padding:4px 20px 12px;display:flex;justify-content:space-between;align-items:center;flex-shrink:0;position:relative;z-index:1}
.sheet-head h2{font-size:22px;font-weight:700;letter-spacing:-.02em}
.sheet-close{width:32px;height:32px;border-radius:50%;background:var(--fill);display:grid;place-items:center;transition:transform 120ms}
.sheet-close:active{transform:scale(.85)}
.sheet-scroll{overflow-y:auto;padding:0 20px 20px;position:relative;z-index:1}
.sheet-scroll::-webkit-scrollbar{width:6px}
.sheet-scroll::-webkit-scrollbar-thumb{background:var(--fill);border-radius:6px}

.detail-block{margin-bottom:18px}
.detail-block h4,.setting-group h4{font-size:13px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.04em;margin-bottom:8px}
.detail-desc{font-size:17px;line-height:1.4;font-weight:500}
.detail-list{border-radius:var(--radius-row);overflow:hidden;background:color-mix(in srgb,var(--text) 5%,transparent)}
.detail-row{display:flex;justify-content:space-between;gap:16px;padding:13px 14px;font-size:15px;position:relative}
.detail-row+.detail-row::before{content:"";position:absolute;left:14px;right:0;top:0;height:.5px;background:var(--separator)}
.detail-row .k{color:var(--text-secondary)}
.detail-row .v{text-align:right;font-weight:500;max-width:60%}
.detail-badges{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 10px}
.btn-primary{width:100%;padding:14px;border-radius:16px;background:var(--blue);color:#fff;font-size:17px;font-weight:600;display:flex;align-items:center;justify-content:center;gap:8px;transition:transform 120ms}
.btn-primary:active{transform:scale(.97)}
.btn-primary svg{width:18px;height:18px}

.setting-group{margin-bottom:18px}
.setting-row{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;font-size:16px}
.seg-control{display:flex;padding:4px;gap:4px}
.seg{flex:1;padding:10px;border-radius:12px;font-size:15px;font-weight:600;color:var(--text-secondary);transition:background 200ms,color 200ms,transform 120ms}
.seg:active{transform:scale(.96)}
.seg.active{background:var(--blue);color:#fff}
.glass-slider{width:100%;-webkit-appearance:none;appearance:none;height:32px;background:transparent;margin:6px 0}
.glass-slider::-webkit-slider-runnable-track{height:6px;border-radius:3px;background:linear-gradient(90deg,var(--teal),var(--blue),var(--purple))}
.glass-slider::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:28px;height:28px;border-radius:50%;background:#fff;margin-top:-11px;box-shadow:0 2px 8px rgba(0,0,0,.4),inset 0 0 0 1px rgba(0,0,0,.1);cursor:pointer}
.glass-level-labels{display:flex;justify-content:space-between;font-size:12px;color:var(--text-secondary);padding:0 4px}
.toggle{width:51px;height:31px;border-radius:999px;background:var(--fill);position:relative;transition:background 200ms;flex-shrink:0;cursor:pointer}
.toggle.on{background:var(--green)}
.toggle::after{content:"";position:absolute;top:2px;left:2px;width:27px;height:27px;border-radius:50%;background:#fff;transition:transform 220ms var(--ease-spring);box-shadow:0 2px 5px rgba(0,0,0,.3)}
.toggle.on::after{transform:translateX(20px)}

#state-overlay{position:fixed;inset:0;z-index:40;display:none;flex-direction:column;align-items:center;justify-content:center;padding:40px;background:rgba(var(--glass-tint-dark),.82)}
#state-overlay.show{display:flex}
#stateContent{display:flex;flex-direction:column;align-items:center;gap:20px;width:100%}
.state-spinner{width:44px;height:44px;border-radius:50%;border:4px solid var(--text-tertiary);border-top-color:var(--blue);animation:spin .9s linear infinite}
.skeleton-group{width:min(420px,90%)}
.skel{border-radius:var(--radius-card);height:78px;margin-bottom:14px;background:linear-gradient(100deg,rgba(255,255,255,.06) 30%,rgba(255,255,255,.14) 50%,rgba(255,255,255,.06) 70%);background-size:200% 100%;animation:shimmer 1.4s infinite}
@keyframes shimmer{to{background-position:-200% 0}}
.error-icon{width:64px;height:64px;color:var(--red)}
.error-icon svg{width:100%;height:100%}
.error-title{font-size:22px;font-weight:700}
.error-msg{font-size:15px;color:var(--text-secondary);text-align:center;max-width:320px;line-height:1.4}
.retry-btn{padding:13px 28px;border-radius:999px;background:var(--blue);color:#fff;font-size:16px;font-weight:600;display:flex;align-items:center;gap:8px;transition:transform 120ms}
.retry-btn:active{transform:scale(.96)}
.retry-btn svg{width:18px;height:18px}
.error-hint{font-size:14px;color:var(--text-secondary);text-align:center;max-width:340px;line-height:1.4;opacity:.9}
.error-actions{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin-top:4px}
.error-actions .retry-btn{margin:0}
.retry-btn.secondary{background:rgba(var(--glass-tint-dark),.55);color:var(--text);border:1px solid rgba(128,128,128,.35)}
.error-details{max-width:360px;width:100%;font-size:12px;color:var(--text-secondary)}
.error-details summary{cursor:pointer;text-align:center;opacity:.8}
.error-details pre{margin-top:8px;max-height:140px;overflow:auto;white-space:pre-wrap;word-break:break-word;text-align:left;padding:10px;border-radius:10px;background:rgba(128,128,128,.15);font-size:11px;user-select:text}
#warnBar{display:none;margin:0 16px 8px;padding:12px 14px;border-radius:16px;border:1px solid rgba(255,159,10,.45);background:rgba(255,159,10,.14);font-size:13.5px;line-height:1.4;gap:10px;align-items:flex-start}
#warnBar.show{display:flex}
#warnBar .warn-ico{width:20px;height:20px;flex:none;color:#ff9f0a;margin-top:1px}
#warnBar .warn-ico svg{width:100%;height:100%}
#warnBar .warn-body{flex:1;min-width:0}
#warnBar .warn-title{font-weight:700}
#warnBar .warn-hint{opacity:.8;margin-top:2px}
#warnBar .warn-btns{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}
#warnBar button{padding:6px 12px;border-radius:999px;font-size:13px;font-weight:600;background:rgba(128,128,128,.22);color:inherit}
#warnBar .warn-x{flex:none;padding:2px 8px;font-size:18px;line-height:1;background:transparent;opacity:.6}

.detail-block details.raw summary{cursor:pointer;font-size:13px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.04em;padding:4px 0 8px;list-style:none}
details.raw summary::-webkit-details-marker{display:none}
details.raw summary::before{content:"\25B8  "}
details.raw[open] summary::before{content:"\25BE  "}
details.raw .detail-row .k{font-size:12px;word-break:break-word;max-width:42%}
details.raw .detail-row .v{font-size:13px;word-break:break-word}
/* frameless window */
:root{__WC_VARS__}
#titlebar{display:none;flex:0 0 36px;height:36px;position:relative;z-index:6;user-select:none;-webkit-user-select:none}
body.framed #titlebar{display:block}
body.framed #header{padding-top:0}
#wc{position:fixed;top:9px;right:14px;z-index:50;display:none;gap:8px}
body.framed #wc{display:flex}
.wc-btn{width:18px;height:18px;padding:0;margin:0;border:0;border-radius:50%;background-color:transparent;background-size:contain;background-repeat:no-repeat;background-position:center;cursor:default;outline:none}
#wcClose{background-image:var(--wc-close)} #wcClose:hover{background-image:var(--wc-close-hover)}
#wcMin{background-image:var(--wc-min)} #wcMin:hover{background-image:var(--wc-min-hover)}
#wcMax{background-image:var(--wc-max)} #wcMax:hover{background-image:var(--wc-max-hover)}
.wc-btn:active{filter:brightness(.88)}
#grips{display:none}
body.framed #grips{display:block}
body.maximized .grip{display:none}
.grip{position:fixed;z-index:60}
.grip[data-edge=n]{top:0;left:12px;right:12px;height:5px;cursor:ns-resize}
.grip[data-edge=s]{bottom:0;left:12px;right:12px;height:5px;cursor:ns-resize}
.grip[data-edge=e]{right:0;top:12px;bottom:12px;width:5px;cursor:ew-resize}
.grip[data-edge=w]{left:0;top:12px;bottom:12px;width:5px;cursor:ew-resize}
.grip[data-edge=ne]{top:0;right:0;width:12px;height:12px;cursor:nesw-resize}
.grip[data-edge=nw]{top:0;left:0;width:12px;height:12px;cursor:nwse-resize}
.grip[data-edge=se]{bottom:0;right:0;width:12px;height:12px;cursor:nwse-resize}
.grip[data-edge=sw]{bottom:0;left:0;width:12px;height:12px;cursor:nesw-resize}
@media (prefers-reduced-motion:reduce){.blob,.skel{animation:none}#scroll{scroll-behavior:auto}*{transition-duration:.01ms !important}#sheet{transition:opacity 200ms linear !important;transform:translate(-50%,0) !important;opacity:0;pointer-events:none}#sheet.show{opacity:1;pointer-events:auto}}
@media (prefers-reduced-transparency:reduce){.glass,.group,#header.scrolled{-webkit-backdrop-filter:none !important;backdrop-filter:none !important;background:var(--bg-elev) !important}.blob{display:none}}
@media (prefers-contrast:more){:root{--text-secondary:var(--text);--separator:var(--separator-strong)}.glass,.group{border-width:1px;border-color:var(--text-secondary)}}
body.reduce-motion *{animation-duration:.01ms !important;transition-duration:.01ms !important}
body.reduce-motion .blob{animation:none}
</style>
</head>
<body>

<div id="wallpaper"><div class="blob b1"></div><div class="blob b2"></div><div class="blob b3"></div><div class="blob b4"></div><div class="blob b5"></div></div>

<div id="wc">
  <button class="wc-btn" id="wcMin" aria-label="Minimize"></button>
  <button class="wc-btn" id="wcMax" aria-label="Maximize"></button>
  <button class="wc-btn" id="wcClose" aria-label="Close"></button>
</div>
<div id="grips"><div class="grip" data-edge="n"></div><div class="grip" data-edge="s"></div><div class="grip" data-edge="e"></div><div class="grip" data-edge="w"></div><div class="grip" data-edge="ne"></div><div class="grip" data-edge="nw"></div><div class="grip" data-edge="se"></div><div class="grip" data-edge="sw"></div></div>

<div id="app">
  <div id="titlebar" class="pywebview-drag-region"></div>
  <header id="header">
    <div class="header-top">
      <div class="header-title-wrap pywebview-drag-region">
        <div class="header-title" id="title">Planner</div>
        <div class="header-subtitle" id="subtitle">Last synced</div>
      </div>
      <div class="header-actions">
        <button class="icon-btn glass" id="searchBtn" aria-label="Search">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>
        </button>
        <button class="icon-btn glass" id="syncBtn" aria-label="Sync">
          <svg id="syncIcon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 1-9 9 9 9 0 0 1-7.5-4M3 12a9 9 0 0 1 9-9 9 9 0 0 1 7.5 4"/><path d="M21 4v5h-5M3 20v-5h5"/></svg>
        </button>
        <button class="icon-btn glass" id="settingsBtn" aria-label="Settings">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/><circle cx="9" cy="6" r="2.2" fill="currentColor"/><circle cx="15" cy="12" r="2.2" fill="currentColor"/><circle cx="8" cy="18" r="2.2" fill="currentColor"/></svg>
        </button>
      </div>
    </div>
  </header>

  <div id="searchbar">
    <input id="searchInput" type="text" autocomplete="off" spellcheck="false" placeholder="Search tasks, notes, lessons and grades...">
    <button id="searchClear" aria-label="Clear search"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg></button>
  </div>
  <div id="chips"></div>
  <div id="warnBar" role="status"></div>
  <main id="scroll"></main>

  <nav id="tabbar" class="glass">
    <div class="bubble" id="bubble"></div>
    <button class="tab active" data-tab="todo">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg><span>To-Do</span>
    </button>
    <button class="tab" data-tab="missed">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg><span>Missed</span>
      <span class="tab-badge" id="missedBadge" style="display:none">0</span>
    </button>
    <button class="tab" data-tab="schedule">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg><span>Schedule</span>
    </button>
    <button class="tab" data-tab="all">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg><span>All Classes</span>
    </button>
    <button class="tab" data-tab="grades">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15a6 6 0 1 0 0-12 6 6 0 0 0 0 12z"/><path d="M8.2 13.5 7 22l5-3 5 3-1.2-8.5"/></svg><span>Grades</span>
    </button>
  </nav>
</div>

<div id="sheet-backdrop"></div>
<div id="sheet" class="glass">
  <div class="sheet-grabber"></div>
  <div class="sheet-head">
    <h2 id="sheetTitle">Detail</h2>
    <button class="sheet-close" id="sheetClose" aria-label="Close"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
  </div>
  <div class="sheet-scroll" id="sheetBody"></div>
</div>

<div id="state-overlay"><div id="stateContent"></div></div>

<script>
/* ===== PYTHON BRIDGE ===== */
var EMBEDDED = __EMBEDDED_JSON__;
var BOOT = __BOOT_JSON__;
var DATA = __DATA_JSON__;
var COMPLETED = __COMPLETED_JSON__;
var SETTINGS = __SETTINGS_JSON__;
var PINNED = __PINNED_JSON__;
var NOTES = __NOTES_JSON__;
var PLATFORM_ID = DATA.platform_id, USER_ID = DATA.user_id;
DATA.todos = DATA.todos || []; DATA.days = DATA.days || []; DATA.all_classes = DATA.all_classes || [];
function bridge(){ return (EMBEDDED && window.pywebview && window.pywebview.api) ? window.pywebview.api : null; }
function syncNow(){ var api = bridge(); if (!api) return; showLoading(); api.sync_now(); }
function markTask(id, done){
  var i = COMPLETED.indexOf(id);
  if (done && i === -1) COMPLETED.push(id);
  if (!done && i !== -1) COMPLETED.splice(i, 1);
  var api = bridge(); if (api) api.mark_task(id, !!done);
  render(DATA, COMPLETED, { keepScroll: true });
}
function openExternal(url){ var api = bridge(); if (api) api.open_external(url); else window.open(url, "_blank"); }
function saveSetting(key, val){
  SETTINGS[key] = val;
  var api = bridge();
  if (api) api.save_setting(key, val);
  else { try { localStorage.setItem("planner.settings", JSON.stringify(SETTINGS)); } catch(e){} }
}
function loadSetting(key){ return (key in SETTINGS) ? SETTINGS[key] : null; }
function togglePin(id){
  var i = PINNED.indexOf(id), on = i === -1;
  if (on) PINNED.push(id); else PINNED.splice(i, 1);
  var api = bridge();
  if (api) api.pin_task(id, on);
  else { try { localStorage.setItem("planner.pinned", JSON.stringify(PINNED)); } catch(e){} }
  return on;
}
function saveNote(id, text){
  text = (text || "").trim();
  if (text) NOTES[id] = text; else delete NOTES[id];
  var api = bridge();
  if (api) api.save_note(id, text);
  else { try { localStorage.setItem("planner.notes", JSON.stringify(NOTES)); } catch(e){} }
}
if (!EMBEDDED) {
  try { var _p = JSON.parse(localStorage.getItem("planner.pinned") || "[]"); if (Array.isArray(_p)) PINNED = _p; } catch(e){}
  try { var _n = JSON.parse(localStorage.getItem("planner.notes") || "{}"); if (_n && typeof _n === "object") NOTES = _n; } catch(e){}
}
if (!EMBEDDED) { try { var _s = JSON.parse(localStorage.getItem("planner.settings") || "{}"); for (var _k in _s) if (!(_k in SETTINGS)) SETTINGS[_k] = _s[_k]; } catch(e){} }

/* ===== STATE ===== */
var activeTab = "todo", activeCourse = "All", completedOpen = false, sheetLink = null;
var TABS = ["todo","missed","schedule","all","grades"];
var TAB_TITLES = { todo:"Planner", missed:"Missed", schedule:"Schedule", all:"All Classes", grades:"Grades" };
var searchQuery = "", noteTimer = null, noteTaskId = null;
DATA.results = DATA.results || [];
function pad(n){ return String(n).padStart(2,"0"); }
function isoOffset(days){ var d=new Date(); d.setHours(0,0,0,0); d.setDate(d.getDate()+days); return d.getFullYear()+"-"+pad(d.getMonth()+1)+"-"+pad(d.getDate()); }
var TODAY = isoOffset(0);
var UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
var PALETTE = ["--blue","--purple","--orange","--green","--teal","--pink","--yellow","--red"];
var COURSE_VAR = { frans:"--purple", geschiedenis:"--orange", nederlands:"--green", english:"--teal", engels:"--teal" };
function courseVar(c){
  c = (c||"").toLowerCase();
  if (COURSE_VAR[c]) return COURSE_VAR[c];
  var h = 0; for (var i=0;i<c.length;i++) h = (h*31 + c.charCodeAt(i)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

/* ===== HELPERS ===== */
function parseDay(s){ return new Date(s + "T00:00:00"); }
function daysBetween(a,b){ return Math.round((parseDay(b) - parseDay(a)) / 86400000); }
function fmtDate(iso){ if(!iso) return "-"; return parseDay(iso).toLocaleDateString("en-GB",{weekday:"short",day:"numeric",month:"short"}); }
function fmtLong(iso){ if(!iso) return "-"; return parseDay(iso).toLocaleDateString("en-GB",{weekday:"long",day:"numeric",month:"long"}); }
function relLabel(iso){
  if (!iso) return "-";
  var d = daysBetween(TODAY, iso);
  if (d===0) return "Today"; if (d===1) return "Tomorrow"; if (d===-1) return "Yesterday";
  if (d>1 && d<7) return "In "+d+" days"; if (d<-1 && d>-7) return Math.abs(d)+" days ago";
  return fmtDate(iso);
}
function esc(s){ return String(s==null?"":s).replace(/[&<>"']/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]; }); }
function isOverdue(t){ return daysBetween(TODAY, t.due_date) < 0; }
function isMissed(t, completed){ return completed.indexOf(t.id)===-1 && isOverdue(t) && daysBetween(TODAY, t.due_date) >= -7; }

var ICON = {
  warn:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  ai:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/></svg>',
  ok:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  clock:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
  cal:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
  ext:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>',
  pin:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 17v5"/><path d="M9 3h6l-1 7 3 3v2H7v-2l3-3z"/></svg>',
  clip:'<svg class="mini" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.4 11.1 12.2 20.3a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5"/></svg>',
  link:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.1 0l3-3a5 5 0 0 0-7.1-7.1l-1.7 1.7"/><path d="M14 11a5 5 0 0 0-7.1 0l-3 3a5 5 0 0 0 7.1 7.1l1.7-1.7"/></svg>',
  note:'<svg class="mini" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>',
  grade:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15a6 6 0 1 0 0-12 6 6 0 0 0 0 12z"/><path d="M8.2 13.5 7 22l5-3 5 3-1.2-8.5"/></svg>',
  search:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>',
  retry:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>'
};

/* ===== RENDER ===== */
// Schedule/All Classes open on today or the next day with an entry
function scrollToToday(){
  if (activeTab !== "schedule" && activeTab !== "all") return;
  var scroll = document.getElementById("scroll");
  var secs = scroll.querySelectorAll(".section[data-date]");
  var target = null;
  for (var i = 0; i < secs.length; i++) { if (secs[i].getAttribute("data-date") >= TODAY) { target = secs[i]; break; } }
  if (!target && secs.length) target = secs[secs.length - 1];
  if (!target) return;
  var top = target.getBoundingClientRect().top - scroll.getBoundingClientRect().top + scroll.scrollTop - 6;
  scroll.style.scrollBehavior = "auto"; scroll.scrollTop = Math.max(0, top); scroll.style.scrollBehavior = "";
}
function render(data, completed, opts){
  opts = opts || {};
  TODAY = isoOffset(0);
  renderWarnings(data);
  var scroll = document.getElementById("scroll");
  var prev = opts.keepScroll ? scroll.scrollTop : 0;
  document.getElementById("title").textContent = TAB_TITLES[activeTab];
  document.getElementById("subtitle").textContent = data.generated_at ? "Last synced - " + new Date(data.generated_at).toLocaleString("en-GB",{hour:"2-digit",minute:"2-digit",day:"numeric",month:"short"}) : "Not synced yet";
  renderChips(data);
  var html = "";
  if (!data.generated_at) html = empty("Not synced yet","Press the sync button at the top right to load your planner.",ICON.clock);
  else if (activeTab==="todo") html = renderTodo(data, completed);
  else if (activeTab==="missed") html = renderMissed(data, completed);
  else if (activeTab==="schedule") html = renderSchedule(data, completed);
  else if (activeTab==="grades") html = renderGrades(data);
  else html = renderAll(data);
  scroll.innerHTML = html;
  if (opts.keepScroll) { scroll.style.scrollBehavior = "auto"; scroll.scrollTop = prev; scroll.style.scrollBehavior = ""; }
  else if (data.generated_at && !searchActive()) scrollToToday();
  var n = data.todos.filter(function(t){ return isMissed(t, completed); }).length;
  var b = document.getElementById("missedBadge");
  b.style.display = n>0 ? "grid" : "none"; b.textContent = n;
  updateTabs();
}

function renderChips(data){
  var el = document.getElementById("chips");
  if (activeTab !== "todo") { el.innerHTML = ""; return; }
  var seen = {}, courses = ["All"];
  data.todos.forEach(function(t){ if (!seen[t.course]) { seen[t.course]=1; courses.push(t.course); } });
  el.innerHTML = courses.map(function(c){ return '<button class="chip'+(c===activeCourse?" active":"")+'" data-course="'+esc(c)+'">'+esc(c)+'</button>'; }).join("");
}

function badges(t){
  var h = "";
  if (t.type) h += '<span class="badge badge-type '+esc(t.type.toLowerCase())+'">'+esc(t.type)+'</span>';
  if (t.due_date_corrected) h += '<span class="badge badge-corrected">'+ICON.warn+' Corrected date</span>';
  if (t.due_date_source==="ai") h += '<span class="badge badge-ai">'+ICON.ai+' AI-detected - verify</span>';
  if (t.warning) h += '<span class="badge badge-warn">'+ICON.warn+' Important</span>';
  return h;
}

/* ----- search ----- */
function searchTerms(){ return searchQuery.toLowerCase().split(/\s+/).filter(Boolean); }
function searchActive(){ return searchTerms().length > 0; }
function matchesText(hay){
  var terms = searchTerms(); if (!terms.length) return true;
  hay = String(hay || "").toLowerCase();
  return terms.every(function(w){ return hay.indexOf(w) !== -1; });
}
function matchTask(t){ return matchesText([t.course, t.type, t.description, t.body, NOTES[t.id]].join(" ")); }
function matchEvent(ev){
  var hay = [ev.course, ev.title, ev.teacher, ev.classroom, ev.groups, ev.note];
  if (ev.info) ev.info.assignments.forEach(function(a){ hay.push(a.type, a.description, a.body, NOTES[a.id]); });
  return matchesText(hay.join(" "));
}
function noMatches(){ return empty("No matches", "Nothing matches &ldquo;"+esc(searchQuery.trim())+"&rdquo;.", ICON.search); }

function taskRow(t, completed){
  var done = completed.indexOf(t.id)!==-1, pinned = PINNED.indexOf(t.id)!==-1;
  var extras = (t.attachments && t.attachments.length ? '<span style="color:var(--text-tertiary)">&middot;</span><span>'+ICON.clip+t.attachments.length+'</span>' : "")+
    (t.weblinks && t.weblinks.length ? '<span style="color:var(--text-tertiary)">&middot;</span><span>'+ICON.clip.replace("mini","mini")+t.weblinks.length+' link'+(t.weblinks.length>1?"s":"")+'</span>' : "");
  var cls = "task-row"+(done?" done":"")+(isOverdue(t)?" overdue":"")+(t.warning?" warning":"");
  return '<div class="'+cls+'" data-detail="task" data-id="'+esc(t.id)+'">'+
    '<div class="check'+(done?" done":"")+(t.warning?" warn-ring":"")+'" data-check="'+esc(t.id)+'"></div>'+
    '<div class="task-body"><div class="task-line1"><span class="task-course">'+esc(t.course)+'</span>'+badges(t)+'</div>'+
    '<div class="task-desc">'+esc(t.description)+'</div>'+
    (infoText(t) ? '<div class="task-info">'+esc(infoText(t))+'</div>' : "")+
    (NOTES[t.id] ? '<div class="task-note">'+ICON.note+esc(NOTES[t.id])+'</div>' : "")+
    '<div class="task-meta"><span>'+relLabel(t.due_date)+'</span><span style="color:var(--text-tertiary)">&middot;</span><span>posted '+fmtDate(t.posted_date)+'</span>'+extras+'</div></div>'+
    '<button class="task-pin'+(pinned?" on":"")+'" data-pin="'+esc(t.id)+'" aria-label="'+(pinned?"Unpin":"Pin")+'" title="'+(pinned?"Unpin":"Pin to top")+'">'+ICON.pin+'</button></div>';
}

function infoText(t){ return t && t.body && t.body.trim() && t.body.trim()!==(t.description||"").trim() ? t.body.trim() : ""; }
function empty(title, msg, icon, compact){ return '<div class="empty'+(compact?" compact":"")+'">'+icon+'<h3>'+title+'</h3><p>'+msg+'</p></div>'; }

/* ----- week ahead: busy days + summary ----- */
var TEST_RE = /toets|evaluatie|test|examen|proef/i;
function weekStats(data, completed){
  var days = [], i;
  for (i = 0; i < 7; i++) days.push({ date: isoOffset(i), n: 0, tests: 0, score: 0 });
  var total = 0, tests = 0;
  data.todos.forEach(function(t){
    if (completed.indexOf(t.id) !== -1) return;
    var k = daysBetween(TODAY, t.due_date);
    if (k < 0 || k > 6) return;
    var isTest = TEST_RE.test(t.type || "");
    days[k].n++; days[k].score += isTest ? 3 : 1; if (isTest) days[k].tests++;
    total++; if (isTest) tests++;
  });
  var peak = 0; days.forEach(function(d, j){ if (d.score > days[peak].score) peak = j; });
  return { days: days, total: total, tests: tests, peak: days[peak].score > 0 ? peak : -1 };
}
function localSummary(w){
  if (!w.total) return "Nothing is due in the next 7 days.";
  var out = w.total + (w.total === 1 ? " task is" : " tasks are") + " due in the next 7 days";
  out += w.tests ? ", including " + w.tests + (w.tests === 1 ? " test or evaluation." : " tests or evaluations.") : ".";
  if (w.peak >= 0) out += " Busiest day: " + parseDay(w.days[w.peak].date).toLocaleDateString("en-GB",{weekday:"long"}) + " (" + w.days[w.peak].n + (w.days[w.peak].n === 1 ? " item" : " items") + ").";
  return out;
}
function renderOverview(data, completed){
  var w = weekStats(data, completed), max = 1;
  w.days.forEach(function(d){ if (d.score > max) max = d.score; });
  var bars = w.days.map(function(d, i){
    var cls = "busy-col" + (d.score === 0 ? " zero" : d.score >= 6 ? " high" : d.score >= 3 ? " mid" : "") + (i === 0 ? " today" : "");
    var label = parseDay(d.date).toLocaleDateString("en-GB",{weekday:"short"});
    var tip = fmtDate(d.date) + ": " + d.n + (d.n === 1 ? " task" : " tasks") + (d.tests ? ", " + d.tests + (d.tests === 1 ? " test" : " tests") : "");
    return '<div class="'+cls+'" title="'+esc(tip)+'"><span class="busy-n">'+(d.n||"")+'</span><div class="busy-bar" style="height:'+Math.max(4, Math.round(d.score / max * 58))+'px"></div><span class="busy-day">'+(i===0?"Today":label)+'</span></div>';
  }).join("");
  return '<div class="section"><div class="section-header">Week ahead</div><div class="group overview">'+
    '<div class="summary-text">'+esc(localSummary(w))+'</div>'+
    '<div class="busy">'+bars+'</div><div class="busy-legend">Busier days are taller &middot; tests count extra</div></div></div>';
}

function renderTodo(data, completed){
  var searching = searchActive();
  function pass(t){ return (activeCourse==="All" || t.course===activeCourse) && matchTask(t); }
  var open = data.todos.filter(function(t){ return completed.indexOf(t.id)===-1 && pass(t); });
  var pinned = open.filter(function(t){ return PINNED.indexOf(t.id)!==-1; });
  var todos = open.filter(function(t){ return PINNED.indexOf(t.id)===-1 && !isOverdue(t); });
  var g = { "Today":[], "Tomorrow":[], "This week":[], "Later":[] };
  todos.forEach(function(t){
    var d = daysBetween(TODAY, t.due_date);
    (d===0 ? g["Today"] : d===1 ? g["Tomorrow"] : d<7 ? g["This week"] : g["Later"]).push(t);
  });
  var html = (!searching && activeCourse==="All") ? renderOverview(data, completed) : "";
  if (pinned.length) html += '<div class="section"><div class="section-header">Pinned<span class="count">'+pinned.length+'</span></div><div class="group">'+pinned.map(function(t){ return taskRow(t, completed); }).join("")+'</div></div>';
  var shown = pinned.length;
  Object.keys(g).forEach(function(k){
    if (!g[k].length) return;
    shown += g[k].length;
    html += '<div class="section"><div class="section-header">'+k+'<span class="count">'+g[k].length+'</span></div><div class="group">'+g[k].map(function(t){ return taskRow(t, completed); }).join("")+'</div></div>';
  });
  var done = data.todos.filter(function(t){ return completed.indexOf(t.id)!==-1 && pass(t); })
    .sort(function(a,b){ return a.due_date < b.due_date ? 1 : -1; });
  if (!shown) html += searching && !done.length ? noMatches()
    : empty("All caught up", done.length ? done.length+" completed. Nothing else due right now." : "Nothing due right now. Enjoy the calm.", ICON.ok, done.length>0);
  if (done.length) html += completedSection(done, completed);
  return html;
}

function completedSection(done, completed){
  return '<div class="section"><button class="completed-toggle'+(completedOpen?" open":"")+'" data-toggle-completed="1"><span>Completed</span><span class="meta">'+done.length+
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 6 15 12 9 18"/></svg></span></button>'+
    (completedOpen ? '<div class="group">'+done.map(function(t){ return taskRow(t, completed); }).join("")+'</div>' : "")+'</div>';
}

function renderMissed(data, completed){
  var list = data.todos.filter(function(t){ return isMissed(t, completed) && matchTask(t); });
  if (!list.length) return searchActive() ? noMatches() : empty("All caught up","No missed tasks from the last 7 days.",ICON.clock);
  return '<div class="section"><div class="section-header">Last 7 days<span class="count">'+list.length+'</span></div><div class="group">'+list.map(function(t){ return taskRow(t, completed); }).join("")+'</div></div>';
}

function lessonRow(ev, completed, withAssign){
  var assign = "";
  if (withAssign && ev.info) ev.info.assignments.forEach(function(a){
    var done = completed.indexOf(a.id)!==-1;
    assign += '<div class="lesson-assign" data-detail="task" data-id="'+esc(a.id)+'"><div class="check'+(done?" done":"")+'" data-check="'+esc(a.id)+'"></div>'+
      '<div><div style="font-weight:500">'+esc(a.description)+'</div><div style="font-size:12px;color:var(--text-secondary);margin-top:4px;display:flex;gap:6px;flex-wrap:wrap;align-items:center">'+badges(a)+' due '+relLabel(a.due_date)+'</div></div></div>';
  });
  var sub = [ev.classroom, ev.teacher, ev.groups].filter(Boolean).map(esc).join(" &middot; ");
  return '<div class="lesson-row" data-detail="lesson" data-moment="'+esc(ev.moment_id)+'">'+
    '<div class="lesson-time">'+esc(ev.start)+'<span class="end">'+esc(ev.end)+'</span></div>'+
    '<div class="lesson-bar" style="background:var('+courseVar(ev.course)+')"></div>'+
    '<div class="lesson-body"><div class="lesson-title">'+esc(ev.course)+(ev.title?' <span style="color:var(--text-secondary);font-weight:400">&middot; '+esc(ev.title)+'</span>':"")+'</div>'+
    '<div class="lesson-sub">'+sub+'</div>'+
    (ev.note?'<div class="lesson-sub" style="color:var(--orange)">Note: '+esc(ev.note)+'</div>':"")+assign+'</div></div>';
}

function dayBlocks(days, completed, withAssign, emptyMsg){
  return days.map(function(day){
    var body = day.events.length ? day.events.map(function(ev){ return lessonRow(ev, completed, withAssign); }).join("") : '<div class="lesson-row" style="cursor:default"><div class="lesson-sub">'+emptyMsg+'</div></div>';
    var tag = day.date===TODAY ? ' <span class="today-tag">Today</span>' : "";
    return '<div class="section" data-date="'+esc(day.date)+'"><div class="section-header">'+fmtLong(day.date)+tag+'</div><div class="group">'+body+'</div></div>';
  }).join("");
}
function filterDays(days){
  if (!searchActive()) return days;
  return days.map(function(d){ return { date: d.date, events: d.events.filter(matchEvent) }; }).filter(function(d){ return d.events.length; });
}
function renderSchedule(data, completed){
  if (!data.days.length) return empty("No schedule","There is nothing on the calendar yet.",ICON.cal);
  var days = filterDays(data.days);
  return days.length ? dayBlocks(days, completed, true, "No lessons") : noMatches();
}
function renderAll(data){
  if (!data.all_classes.length) return empty("No classes","There are no classes scheduled.",ICON.cal);
  var days = filterDays(data.all_classes);
  return days.length ? dayBlocks(days, COMPLETED, false, "No classes") : noMatches();
}

/* ----- grades ----- */
function fmtNum(n){ return (Math.round(n * 100) / 100).toString().replace(".", ","); }
function gradeColor(p){ return p == null ? "var(--text)" : p < 50 ? "var(--red)" : p < 70 ? "var(--orange)" : "var(--green)"; }
var GRADE_COLORS = { green:"#34c759", red:"#ff3b30", olive:"#8a9a2b", yellow:"#ffcc00", steel:"#7d93a8", grass:"#5fbf3f", orange:"#ff9500", blue:"#0a84ff", purple:"#af52de", pink:"#ff2d55", teal:"#30b0c7", grey:"#8e8e93", gray:"#8e8e93" };
function gradeCssColor(c){
  c = String(c || "").toLowerCase();
  if (GRADE_COLORS[c]) return GRADE_COLORS[c];
  return /^#[0-9a-f]{3,8}$/.test(c) || /^[a-z]{3,20}$/.test(c) ? c : "";   // hex or CSS colour name only
}
function hasScore(r){ return (r.score != null && r.max) || r.percent != null; }
function colorSquare(r){
  var css = gradeCssColor(r.color);
  return css ? '<span class="grade-square" style="background:'+esc(css)+'" title="'+esc([r.text, r.label].filter(Boolean).join(" - ") || r.color)+'"></span>' : "";
}
function gradeScore(r){ return (r.score != null && r.max) ? fmtNum(r.score) + " / " + fmtNum(r.max) : r.percent != null ? Math.round(r.percent) + "%" : (r.text || "-"); }
function averageOf(list){
  var sum = 0, max = 0;
  list.forEach(function(r){ if (r.counts && r.score != null && r.max > 0) { sum += r.score; max += r.max; } });
  return max > 0 ? sum / max * 100 : null;
}
function avgPill(p){ return p == null ? "" : '<span class="avg-pill" style="color:'+gradeColor(p)+'">'+Math.round(p)+'%</span>'; }
function renderGrades(data){
  var all = data.results || [];
  var list = all.filter(function(r){ return matchesText([r.name, r.course, r.teacher, r.period, (r.feedback||[]).join(" ")].join(" ")); });
  if (!list.length) {
    if (searchActive() && all.length) return noMatches();
    return empty("No grades", esc(data.results_note || "No published grades were found yet. They show up here after a sync."), ICON.grade);
  }
  var by = {};
  list.forEach(function(r){ (by[r.course] = by[r.course] || []).push(r); });
  var overall = averageOf(list);
  var html = overall == null ? "" : '<div class="section"><div class="group grade-summary"><span style="color:var(--text-secondary);font-size:14px;font-weight:600">Overall average</span><b style="color:'+gradeColor(overall)+'">'+Math.round(overall)+'%</b></div></div>';
  Object.keys(by).sort().forEach(function(c){
    html += '<div class="section"><div class="section-header"><span>'+esc(c)+avgPill(averageOf(by[c]))+'</span><span class="count">'+by[c].length+'</span></div><div class="group">'+
      by[c].map(function(r){
        return '<div class="grade-row" data-detail="grade" data-id="'+esc(r.id)+'"><div><div class="grade-name">'+esc(r.name || "Evaluation")+'</div><div class="grade-meta">'+esc(fmtDate(r.date))+(r.counts ? "" : " &middot; doesn&rsquo;t count")+'</div></div>'+
          '<div>'+(!hasScore(r) && colorSquare(r) ? colorSquare(r) : '<div class="grade-score" style="color:'+gradeColor(r.percent)+'">'+esc(gradeScore(r))+'</div>')+(r.percent != null && r.score != null ? '<div class="grade-pct">'+Math.round(r.percent)+'%</div>' : "")+'</div></div>';
      }).join("")+'</div></div>';
  });
  return html;
}
function openGrade(id){
  var r = (DATA.results || []).filter(function(x){ return x.id === id; })[0]; if (!r) return;
  var pairs = [["Course", r.course], ["Date", r.date ? fmtLong(r.date) : "-"]];
  if (hasScore(r) || !colorSquare(r)) pairs.push(["Score", gradeScore(r)]);
  if (r.percent != null) pairs.push(["Percentage", Math.round(r.percent * 10) / 10 + "%"]);
  pairs.push(["Counts toward total", r.counts ? "Yes" : "No"], ["Period", r.period], ["Teacher", r.teacher]);
  var fb = (r.feedback || []).length ? '<div class="detail-block"><h4>Feedback</h4><div class="detail-info">'+esc(r.feedback.join("\n\n"))+'</div></div>' : "";
  showSheet(r.course + " - " + (r.name || "Evaluation"),
    '<div class="detail-block"><div class="detail-desc">'+esc(r.name || "Evaluation")+'</div></div>'+
    (!hasScore(r) && colorSquare(r) ? '<div class="detail-block"><h4>Result</h4><div style="display:flex;align-items:center;gap:12px;font-size:17px;font-weight:600">'+colorSquare(r)+'<span>'+esc([r.text, r.label].filter(Boolean).join(" - "))+'</span></div></div>' : "")+
    '<div class="detail-block"><h4>Details</h4><div class="detail-list">'+rows(pairs)+'</div></div>'+fb);
}

function updateTabs(){
  document.querySelectorAll(".tab").forEach(function(t){ t.classList.toggle("active", t.dataset.tab===activeTab); });
  document.getElementById("bubble").style.transform = "translateX(" + (TABS.indexOf(activeTab)*100) + "%)";
}

/* ===== DETAIL SHEET ===== */
function rows(pairs){ return pairs.map(function(p){ return '<div class="detail-row"><span class="k">'+esc(p[0])+'</span><span class="v">'+esc(p[1]==null||p[1]===""?"-":p[1])+'</span></div>'; }).join(""); }

// user id is already composite ("148_7997_0"); build it only from a bare number
function userSegment(){ var u = String(USER_ID); return /^\d+_\d+_\d+$/.test(u) ? u : PLATFORM_ID + "_" + u + "_0"; }
function deepLink(item, postedDate){
  if (!DATA.main_url) return null;
  var generic = "https://" + DATA.main_url + "/planner";
  var src = item && (item.element_source || item.source);
  var usable = PLATFORM_ID != null && USER_ID != null && item && item.moment_id && UUID_RE.test(item.moment_id) && src === "planner_api" && postedDate;
  if (!usable) return generic;
  var type = /^planned-[a-z-]+$/.test(item.element_type || "") ? item.element_type : "planned-assignments";
  return "https://" + DATA.main_url + "/planner/main/user/" + userSegment() + "/" + postedDate + "/" + type + "/" + PLATFORM_ID + "/" + item.moment_id;
}
function extraBlock(fields){
  if (!fields || !fields.length) return "";
  return '<div class="detail-block"><details class="raw"><summary>Everything Smartschool sent ('+fields.length+')</summary><div class="detail-list">'+rows(fields)+'</div></details></div>';
}
function linkButton(link){ return link ? '<button class="btn-primary" data-external="1">'+ICON.ext+' Open in Smartschool</button>' : ""; }

function fmtSize(n){ if (n == null) return ""; return n >= 1048576 ? (n/1048576).toFixed(1)+" MB" : n >= 1024 ? Math.round(n/1024)+" KB" : n+" B"; }
function linksBlock(t){
  var a = t.attachments || [], w = t.weblinks || [];
  if (!a.length && !w.length) return "";
  var h = '<div class="detail-block"><h4>Attachments &amp; links</h4><div>';
  a.forEach(function(x){
    var label = esc(x.name) + (x.size != null ? ' <span style="color:var(--text-secondary)">('+fmtSize(x.size)+')</span>' : "");
    h += x.url ? '<span class="chip-link" data-open-url="'+esc(x.url)+'">'+ICON.clip.replace(' class="mini"',"")+label+'</span>'
               : '<span class="chip-link static">'+ICON.clip.replace(' class="mini"',"")+label+'</span>';
  });
  w.forEach(function(x){
    var label = esc(x.name || x.url);
    h += x.url ? '<span class="chip-link" data-open-url="'+esc(x.url)+'">'+ICON.link+label+'</span>' : '<span class="chip-link static">'+ICON.link+label+'</span>';
  });
  return h + '</div>' + (a.some(function(x){ return !x.url; }) ? '<div style="font-size:12px;color:var(--text-secondary)">Open the task in Smartschool to download attachments.</div>' : "") + '</div>';
}
function noteBlock(id){
  return '<div class="detail-block"><h4>My notes</h4><textarea class="note-area" id="noteArea" data-note="'+esc(id)+'" placeholder="Private notes - saved on this computer only">'+esc(NOTES[id] || "")+'</textarea></div>';
}
function pinButton(id){
  var on = PINNED.indexOf(id) !== -1;
  return '<button class="btn-secondary" data-pin-sheet="'+esc(id)+'">'+ICON.pin.replace('<svg ','<svg class="pin-ic" ')+(on ? " Unpin from top" : " Pin to top")+'</button>';
}
function flushNote(){
  if (noteTimer) { clearTimeout(noteTimer); noteTimer = null; }
  var area = document.getElementById("noteArea");
  if (area && area.getAttribute("data-note") && (NOTES[area.getAttribute("data-note")] || "") !== area.value.trim()) {
    saveNote(area.getAttribute("data-note"), area.value);
    render(DATA, COMPLETED, { keepScroll: true });
  }
}

function openTask(id){
  var t = DATA.todos.filter(function(x){ return x.id===id; })[0], lesson = null, day = null;
  if (!t) DATA.days.forEach(function(d){ d.events.forEach(function(ev){ if (ev.info) ev.info.assignments.forEach(function(a){ if (a.id===id && !t) { t=a; lesson=ev; day=d; } }); }); });
  if (!t) return;
  var link = lesson ? deepLink(lesson, day.date) : deepLink(t, t.posted_date);
  var pairs = [["Course",t.course||(lesson&&lesson.course)],["Type",t.type],["Posted",t.posted_date?fmtLong(t.posted_date):"-"],["Due",t.due_date ? fmtLong(t.due_date)+" ("+relLabel(t.due_date)+")" : "-"]];
  pairs.push(["Status", COMPLETED.indexOf(t.id)!==-1 ? "Done" : "Not done"]);
  if (t.due_date_source && t.due_date_source!=="none") pairs.push(["Date source", t.due_date_source+(t.due_date_corrected?" - corrected":"")]);
  if (lesson) pairs.push(["Teacher",lesson.teacher],["Classroom",lesson.classroom],["Class",lesson.groups]);
  var body = '<div class="detail-block"><div class="detail-badges">'+badges(t)+'</div><div class="detail-desc">'+esc(t.description)+'</div></div>'+
    (infoText(t) ? '<div class="detail-block"><h4>Info voor de leerling</h4><div class="detail-info">'+esc(infoText(t))+'</div></div>' : "")+
    linksBlock(t)+noteBlock(t.id)+
    '<div class="detail-block"><h4>Details</h4><div class="detail-list">'+rows(pairs)+'</div></div>'+
    extraBlock(t.detail_fields)+pinButton(t.id)+linkButton(link);
  showSheet((t.course||(lesson&&lesson.course)||"Task")+" - "+(t.type||"Task"), body, link);
}

function openLesson(mid){
  var ev = null, day = null;
  DATA.days.concat(DATA.all_classes).forEach(function(d){ d.events.forEach(function(e){ if (e.moment_id===mid && !ev) { ev=e; day=d; } }); });
  if (!ev) return;
  var link = deepLink(ev, day.date);
  var fields = (ev.detail_fields || []).slice();
  var assign = "";
  if (ev.info && ev.info.assignments && ev.info.assignments.length) {
    ev.info.assignments.forEach(function(a){ fields = fields.concat(a.detail_fields || []); });
    ev.info.assignments.forEach(function(a){ if (infoText(a)) assign += '<div class="detail-block"><h4>Info voor de leerling</h4><div class="detail-info">'+esc(infoText(a))+'</div></div>'; });
    assign += '<div class="detail-block"><h4>Assignments</h4><div class="detail-list">'+ev.info.assignments.map(function(a){
      return '<div class="detail-row" style="cursor:pointer" data-detail="task" data-id="'+esc(a.id)+'"><span class="k">'+esc(a.type||"Task")+'</span><span class="v">'+esc(a.description)+' - '+relLabel(a.due_date)+'</span></div>'; }).join("")+'</div></div>';
  }
  var pairs = [["Course",ev.course],["Time",ev.start+" - "+ev.end],["Classroom",ev.classroom],["Teacher",ev.teacher],["Group",ev.groups],["Date",fmtLong(day.date)]];
  if (ev.info && ev.info.materials) pairs.push(["Materials",ev.info.materials]);
  var body = '<div class="detail-block"><div class="detail-desc">'+esc(ev.title||ev.course)+'</div></div>'+
    '<div class="detail-block"><h4>Lesson</h4><div class="detail-list">'+rows(pairs)+'</div></div>'+
    (ev.note?'<div class="detail-block"><h4>Note</h4><div class="detail-desc" style="color:var(--orange)">'+esc(ev.note)+'</div></div>':"")+
    assign+extraBlock(fields)+linkButton(link);
  showSheet(ev.course+" - Lesson", body, link);
}

function showSheet(title, body, link){
  sheetLink = link || null;
  document.getElementById("sheetTitle").textContent = title;
  document.getElementById("sheetBody").innerHTML = body; document.getElementById("sheetBody").scrollTop = 0;
  document.getElementById("sheet").classList.add("show"); document.body.classList.add("sheet-open");
  document.getElementById("sheet-backdrop").classList.add("show");
}
function hideSheet(){ flushNote(); document.body.classList.remove("sheet-open"); document.getElementById("sheet").classList.remove("show"); document.getElementById("sheet-backdrop").classList.remove("show"); }

/* ===== SETTINGS ===== */
function currentLevel(){ var l = loadSetting("glassLevel"); return l==null ? 1 : l; }

function openSettings(){
  var st = document.documentElement.getAttribute("data-style") || "vivid";
  var body =
    '<div class="setting-group"><h4>Appearance</h4><div class="detail-list"><div class="seg-control">'+
      '<button class="seg'+(st==="vivid"?" active":"")+'" data-style-opt="vivid">Vivid</button>'+
      '<button class="seg'+(st==="frost"?" active":"")+'" data-style-opt="frost">Frosted</button></div></div></div>'+
    '<div class="setting-group"><h4>Liquid glass</h4><div class="detail-list"><div style="padding:14px 16px">'+
      '<input type="range" min="0" max="2" step="1" value="'+currentLevel()+'" class="glass-slider" id="glassSlider">'+
      '<div class="glass-level-labels"><span>Clear</span><span>Balanced</span><span>Tinted</span></div></div></div></div>'+
    '<div class="setting-group"><h4>Accessibility</h4><div class="detail-list"><div class="setting-row"><span>Reduce motion</span><div class="toggle'+(loadSetting("reduceMotion")?" on":"")+'" id="motionToggle"></div></div></div></div>'+
    (DATA.main_url ? '<div class="setting-group"><h4>Account</h4><div class="detail-list">'+rows([["School",DATA.main_url]])+'</div></div>'+
    '<button class="btn-primary" data-external="1">'+ICON.ext+' Open in Smartschool</button>' : "");
  showSheet("Settings", body);
  var slider = document.getElementById("glassSlider");
  slider.addEventListener("input", function(){ var v = parseInt(slider.value,10); applyGlassLevel(v); saveSetting("glassLevel", v); });
  var tog = document.getElementById("motionToggle");
  tog.addEventListener("click", function(){ var on = !tog.classList.contains("on"); tog.classList.toggle("on", on); document.body.classList.toggle("reduce-motion", on); saveSetting("reduceMotion", on); });
}

function setStyle(style){
  var app = document.getElementById("app");
  app.style.opacity = ".55";
  document.documentElement.setAttribute("data-style", style);
  saveSetting("style", style);
  applyGlassLevel(currentLevel());
  document.querySelectorAll("[data-style-opt]").forEach(function(el){ el.classList.toggle("active", el.dataset.styleOpt===style); });
  setTimeout(function(){ app.style.opacity = ""; }, 120);
}

function applyGlassLevel(level){
  var frost = document.documentElement.getAttribute("data-style")==="frost";
  var light = matchMedia("(prefers-color-scheme: light)").matches;
  var vivid = [{op:.32,blur:30,sat:180,spec:1},{op:.55,blur:26,sat:170,spec:.9},{op:.78,blur:22,sat:160,spec:.7}];
  var ice   = [{op:.45,blur:40,sat:105,spec:1},{op:.62,blur:34,sat:110,spec:.85},{op:.80,blur:30,sat:120,spec:.65}];
  var m = (frost ? ice : vivid)[level] || (frost ? ice : vivid)[1];
  var r = document.documentElement.style;
  r.setProperty("--glass-opacity", m.op);
  r.setProperty("--glass-blur", m.blur+"px");
  r.setProperty("--glass-saturate", m.sat+"%");
  r.setProperty("--glass-specular", m.spec);
  r.setProperty("--glass-tint-dark", frost ? (light ? "228, 236, 246" : "28, 36, 48") : (light ? "255, 255, 255" : "18, 18, 28"));
}

/* ===== LOADING / ERROR ===== */
function showLoading(label){
  document.getElementById("stateContent").innerHTML = '<div class="state-spinner"></div><div style="font-size:17px;font-weight:600">'+esc(label||"Syncing...")+'</div><div class="skeleton-group"><div class="skel"></div><div class="skel"></div><div class="skel"></div></div>';
  document.getElementById("state-overlay").classList.add("show");
}
function showError(info){
  if (typeof info === "string") info = {title:"Could not sync", message:info};
  info = info || {};
  var kind = info.kind || "unknown";
  var canFix = kind === "login" || kind === "config";
  var h = '<div class="error-icon">'+ICON.warn+'</div><div class="error-title">'+esc(info.title||"Could not sync")+'</div>'
        + '<div class="error-msg">'+esc(info.message||"Something went wrong while loading your planner.")+'</div>';
  if (info.hint) h += '<div class="error-hint">'+esc(info.hint)+'</div>';
  h += '<div class="error-actions">';
  if (canFix) h += '<button class="retry-btn" id="fixBtn">Change login details</button>';
  h += '<button class="retry-btn'+(canFix?' secondary':'')+'" id="retryBtn">'+ICON.retry+' Retry</button>';
  if (DATA && DATA.generated_at) h += '<button class="retry-btn secondary" id="closeErrBtn">Close</button>';
  h += '</div>';
  if (info.details) h += '<details class="error-details"><summary>Technical details</summary><pre>'+esc(String(info.details).slice(-2500))+'</pre></details>';
  document.getElementById("stateContent").innerHTML = h;
  document.getElementById("retryBtn").addEventListener("click", syncNow);
  var fb = document.getElementById("fixBtn");
  if (fb) fb.addEventListener("click", function(){ var api = bridge(); if (api && api.open_setup) { showLoading("Waiting for login details..."); api.open_setup(); } });
  var cb = document.getElementById("closeErrBtn");
  if (cb) cb.addEventListener("click", hideState);
  document.getElementById("state-overlay").classList.add("show");
}
var WARN_DISMISSED = {};
function renderWarnings(data){
  var bar = document.getElementById("warnBar"); if (!bar) return;
  var list = ((data && data.warnings) || []).filter(function(w){ return !WARN_DISMISSED[w.kind]; });
  if (!list.length) { bar.className = ""; bar.innerHTML = ""; return; }
  var w = list[0];
  var h = '<div class="warn-ico">'+ICON.warn+'</div><div class="warn-body"><div class="warn-title">'+esc(w.title||"Heads up")+'</div><div>'+esc(w.message||"")+'</div>';
  if (w.hint) h += '<div class="warn-hint">'+esc(w.hint)+'</div>';
  if (w.fix) h += '<div class="warn-btns"><button id="warnFix">Change login details</button></div>';
  h += '</div><button class="warn-x" id="warnX" aria-label="Dismiss">&times;</button>';
  bar.innerHTML = h; bar.className = "show";
  document.getElementById("warnX").addEventListener("click", function(){ WARN_DISMISSED[w.kind] = true; renderWarnings(data); });
  var f = document.getElementById("warnFix");
  if (f) f.addEventListener("click", function(){ var api = bridge(); if (api && api.open_setup) { api.open_setup(); } });
}
function hideState(){ document.getElementById("state-overlay").classList.remove("show"); }

/* ===== EVENTS ===== */
document.getElementById("tabbar").addEventListener("click", function(e){
  var tab = e.target.closest(".tab"); if (!tab) return;
  activeTab = tab.dataset.tab; activeCourse = "All";
  var s = document.getElementById("scroll"); s.style.scrollBehavior = "auto"; s.scrollTop = 0; s.style.scrollBehavior = "";
  render(DATA, COMPLETED);
});
document.getElementById("chips").addEventListener("click", function(e){
  var c = e.target.closest(".chip"); if (!c) return;
  activeCourse = c.dataset.course; render(DATA, COMPLETED);
});
document.getElementById("syncBtn").addEventListener("click", function(){
  var icon = document.getElementById("syncIcon"); icon.classList.add("sync-spin"); syncNow();
  setTimeout(function(){ icon.classList.remove("sync-spin"); }, 2000);
});
document.getElementById("settingsBtn").addEventListener("click", openSettings);

/* search */
function openSearch(){ document.body.classList.add("searching"); var i = document.getElementById("searchInput"); i.focus(); i.select(); }
function closeSearch(){
  document.body.classList.remove("searching");
  var i = document.getElementById("searchInput"); i.value = "";
  if (searchQuery) { searchQuery = ""; render(DATA, COMPLETED); }
}
function runSearch(){
  searchQuery = document.getElementById("searchInput").value;
  var sc = document.getElementById("scroll"); sc.style.scrollBehavior = "auto"; sc.scrollTop = 0; sc.style.scrollBehavior = "";
  render(DATA, COMPLETED);
}
document.getElementById("searchBtn").addEventListener("click", function(){ document.body.classList.contains("searching") ? closeSearch() : openSearch(); });
document.getElementById("searchInput").addEventListener("input", runSearch);
document.getElementById("searchClear").addEventListener("click", function(){ var i = document.getElementById("searchInput"); i.value = ""; runSearch(); i.focus(); });
document.addEventListener("keydown", function(e){
  var sheetOpen = document.getElementById("sheet").classList.contains("show");
  if ((e.ctrlKey || e.metaKey) && (e.key === "f" || e.key === "F")) { e.preventDefault(); openSearch(); return; }
  if (e.key === "Escape" && !sheetOpen && document.body.classList.contains("searching")) closeSearch();
});
document.getElementById("sheetClose").addEventListener("click", hideSheet);
document.getElementById("sheet-backdrop").addEventListener("click", hideSheet);
document.addEventListener("keydown", function(e){ if (e.key==="Escape") hideSheet(); });

function openSmartschool(){ var url = sheetLink || (DATA.main_url ? "https://" + DATA.main_url + "/planner" : null); if (url) openExternal(url); }
document.getElementById("scroll").addEventListener("click", function(e){
  var pin = e.target.closest("[data-pin]");
  if (pin) { e.stopPropagation(); togglePin(pin.dataset.pin); render(DATA, COMPLETED, { keepScroll: true }); return; }
  if (e.target.closest("[data-toggle-completed]")) { completedOpen = !completedOpen; render(DATA, COMPLETED, { keepScroll: true }); return; }
  var chk = e.target.closest("[data-check]");
  if (chk) {
    e.stopPropagation();
    var id = chk.dataset.check, now = COMPLETED.indexOf(id)===-1, row = chk.closest(".task-row");
    if (now && row && (activeTab==="todo" || activeTab==="missed")) { chk.classList.add("done"); row.classList.add("leaving"); setTimeout(function(){ markTask(id, true); }, 260); }
    else markTask(id, now);
    return;
  }
  var td = e.target.closest("[data-detail='task']"); if (td) { openTask(td.dataset.id); return; }
  var ld = e.target.closest("[data-detail='lesson']"); if (ld) { openLesson(ld.dataset.moment); return; }
  var gd = e.target.closest("[data-detail='grade']"); if (gd) { openGrade(gd.dataset.id); }
});
document.getElementById("sheetBody").addEventListener("input", function(e){
  if (e.target.id !== "noteArea") return;
  noteTaskId = e.target.getAttribute("data-note");
  if (noteTimer) clearTimeout(noteTimer);
  noteTimer = setTimeout(flushNote, 500);
});
document.getElementById("sheetBody").addEventListener("click", function(e){
  var ou = e.target.closest("[data-open-url]"); if (ou) { openExternal(ou.getAttribute("data-open-url")); return; }
  var ps = e.target.closest("[data-pin-sheet]");
  if (ps) {
    var on = togglePin(ps.dataset.pinSheet);
    ps.lastChild.textContent = on ? " Unpin from top" : " Pin to top";
    render(DATA, COMPLETED, { keepScroll: true });
    return;
  }
  if (e.target.closest("[data-external]")) { openSmartschool(); return; }
  var so = e.target.closest("[data-style-opt]"); if (so) { setStyle(so.dataset.styleOpt); return; }
  var td = e.target.closest("[data-detail='task']"); if (td) { openTask(td.dataset.id); }
});
document.getElementById("scroll").addEventListener("scroll", function(){
  document.getElementById("header").classList.toggle("scrolled", this.scrollTop > 8);
});
document.addEventListener("visibilitychange", function(){
  document.body.classList.toggle("page-hidden", document.hidden);
});
matchMedia("(prefers-color-scheme: light)").addEventListener("change", function(){ applyGlassLevel(currentLevel()); });

/* ===== WINDOW CONTROLS ===== */
function winCall(name){ var api = bridge(); return (api && api[name]) ? api[name].apply(api, [].slice.call(arguments, 1)) : null; }
document.getElementById("wcClose").addEventListener("click", function(){ winCall("win_close"); });
document.getElementById("wcMin").addEventListener("click", function(){ winCall("win_minimize"); });
document.getElementById("wcMax").addEventListener("click", function(){ winCall("win_toggle_maximize"); });
document.getElementById("titlebar").addEventListener("dblclick", function(){ winCall("win_toggle_maximize"); });

// edge/corner resize grips (no native resize border)
Array.prototype.forEach.call(document.querySelectorAll(".grip"), function(grip){
  grip.addEventListener("pointerdown", function(ev){
    var api = bridge();
    if (!api || ev.button !== 0) return;
    ev.preventDefault();
    var edge = grip.getAttribute("data-edge"), sx = ev.screenX, sy = ev.screenY;
    var dx = 0, dy = 0, start = null, busy = false, lastW = 0, lastH = 0, MIN_W = 760, MIN_H = 560;
    try { grip.setPointerCapture(ev.pointerId); } catch(e){}
    Promise.resolve(api.win_size()).then(function(sz){ start = sz; lastW = sz.w; lastH = sz.h; flush(); });
    function flush(){
      if (busy || !start) return;
      var w = start.w, h = start.h;
      if (edge.indexOf("e") >= 0) w = start.w + dx;
      if (edge.indexOf("w") >= 0) w = start.w - dx;
      if (edge.indexOf("s") >= 0) h = start.h + dy;
      if (edge.indexOf("n") >= 0) h = start.h - dy;
      w = Math.max(MIN_W, Math.round(w)); h = Math.max(MIN_H, Math.round(h));
      if (w === lastW && h === lastH) return;
      lastW = w; lastH = h; busy = true;
      var done = function(){ busy = false; flush(); };
      Promise.resolve(api.win_resize(w, h, edge)).then(done, done);   // one call at a time
    }
    function move(e){ if (e.buttons === 0) { up(); return; } dx = e.screenX - sx; dy = e.screenY - sy; flush(); }
    function up(){ grip.removeEventListener("pointermove", move); grip.removeEventListener("pointerup", up); grip.removeEventListener("pointercancel", up); try { grip.releasePointerCapture(ev.pointerId); } catch(e){} }
    grip.addEventListener("pointermove", move); grip.addEventListener("pointerup", up); grip.addEventListener("pointercancel", up);
  });
});

/* ===== INIT ===== */
(function(){
  var st = loadSetting("style"); if (st === "vivid" || st === "frost") document.documentElement.setAttribute("data-style", st);
  if (loadSetting("reduceMotion")) document.body.classList.add("reduce-motion");
  if (!EMBEDDED) document.getElementById("syncBtn").style.display = "none";
  if (EMBEDDED) {
    document.body.classList.add("framed");
    var _m = winCall("win_is_maximized");
    if (_m) Promise.resolve(_m).then(function(v){ document.body.classList.toggle("maximized", !!v); });
  }
  applyGlassLevel(currentLevel());
  if (BOOT && BOOT.mode === "loading") { showLoading(BOOT.label); return; }
  if (BOOT && BOOT.mode === "error") { showError(BOOT.error || BOOT.message); return; }
  render(DATA, COMPLETED);
})();
</script>
</body>
</html>
'''


def _assets_dir() -> Path:
    """assets/ next to this file (sys._MEIPASS/assets in the exe)."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "assets"
    return Path(__file__).parent / "assets"


_WINDOW_BUTTONS = {
    # css var: (file, fallback colour)
    "--wc-close": ("close.svg", "#ff5f57"),
    "--wc-close-hover": ("close_hover.svg", "#ff5f57"),
    "--wc-min": ("minimize.svg", "#febc2e"),
    "--wc-min-hover": ("minimize_hover.svg", "#febc2e"),
    "--wc-max": ("maximize.svg", "#28c840"),
    "--wc-max-hover": ("maximize_hover.svg", "#28c840"),
}


def _window_button_css() -> str:
    """CSS variables holding the window-button SVGs as data URIs (coloured circles if missing)."""
    out = []
    for var, (filename, fallback) in _WINDOW_BUTTONS.items():
        path = _assets_dir() / filename
        try:
            b64 = base64.b64encode(path.read_bytes()).decode("ascii")
            out.append(f'{var}:url("data:image/svg+xml;base64,{b64}");')
        except OSError:
            out.append(f"{var}:radial-gradient(circle,{fallback} 0 62%,transparent 64%);")
    return "".join(out)


def _json(obj) -> str:
    # safe inside <script>
    return (
        json.dumps(obj, ensure_ascii=False)
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


_EMPTY_DATA = {"todos": [], "days": [], "all_classes": [], "main_url": "", "generated_at": None}


def _build(data, completed_ids, embedded, settings, boot, pinned=None, notes=None) -> str:
    return (
        TEMPLATE.replace("__WC_VARS__", _window_button_css())
        .replace("__EMBEDDED_JSON__", "true" if embedded else "false")
        .replace("__BOOT_JSON__", _json(boot))
        .replace("__DATA_JSON__", _json(data))
        .replace("__COMPLETED_JSON__", _json(list(completed_ids)))
        .replace("__SETTINGS_JSON__", _json(settings or {}))
        .replace("__PINNED_JSON__", _json(list(pinned or [])))
        .replace("__NOTES_JSON__", _json(notes or {}))
    )


def render_html(
    data: dict,
    completed_ids,
    embedded: bool,
    settings: dict | None = None,
    pinned=None,
    notes: dict | None = None,
) -> str:
    return _build(data, completed_ids, embedded, settings, None, pinned, notes)


def render_loading(settings: dict | None = None, label: str = "Syncing...") -> str:
    return _build(_EMPTY_DATA, [], True, settings, {"mode": "loading", "label": label})


def render_error(info, settings: dict | None = None) -> str:
    """info: a message string, or a dict with kind/title/message/hint/details (see app_errors.explain)."""
    if isinstance(info, str):
        info = {"kind": "unknown", "title": "Could not sync", "message": info}
    return _build(_EMPTY_DATA, [], True, settings, {"mode": "error", "error": info, "message": info.get("message", "")})
