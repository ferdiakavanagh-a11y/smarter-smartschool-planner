"""Shared HTML/CSS/JS for the planner UI, used by build_dashboard.py (read-only) and desktop_app.py (interactive).

render_html(data, completed_ids, embedded, settings) builds the page; embedded=True uses pywebview's
bridge, False works locally in a browser. The UI lives in TEMPLATE."""

from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

TEMPLATE = r'''<!DOCTYPE html>
<html lang="en" data-style="vivid">
<head>
<meta charset="UTF-8" />
<meta name="color-scheme" content="dark light">
<script>document.documentElement.setAttribute("data-scheme",matchMedia("(prefers-color-scheme: light)").matches?"light":"dark")</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Planner</title>
<style>
:root{color-scheme:dark;
--blue:#0A84FF;--orange:#FF9F0A;--purple:#BF5AF2;--red:#FF453A;--green:#30D158;--yellow:#FFD60A;--teal:#64D2FF;--pink:#FF375F;
--glass-opacity:.55;--glass-blur:26px;--glass-saturate:170%;--glass-specular:.9;
--glass-tint:255,255,255;--glass-tint-dark:18,18,28;
--gloss:220,230,246;--gloss-border:.17;--gloss-hi:.22;--gloss-hi-sm:.16;
--glass-inner:rgba(0,0,0,.25);--glass-drop:rgba(0,0,0,.45);--glass-drop-sm:rgba(0,0,0,.35);
--bg:#000;--bg-elev:#1c1c1e;--separator:rgba(255,255,255,.08);--separator-strong:rgba(255,255,255,.18);
--text:#fff;--text-secondary:rgba(240,240,250,.78);--text-tertiary:rgba(235,235,245,.3);--fill:rgba(120,120,128,.32);
--radius-card:24px;--radius-row:18px;--radius-chip:999px;--radius-sheet:30px;
--ease-spring:cubic-bezier(.34,1.56,.64,1);--ease-out:cubic-bezier(.22,1,.36,1);--dur:300ms;--tab-count:6;
--font:"SF Pro Display","SF Pro Text","Segoe UI Variable","Segoe UI",system-ui,-apple-system,sans-serif;
}
:root[data-scheme="light"]{color-scheme:light;
--blue:#007AFF;--orange:#FF9500;--purple:#AF52DE;--red:#FF3B30;--green:#34C759;--yellow:#FFCC00;--teal:#5AC8FA;--pink:#FF2D55;
--bg:#f2f2f7;--bg-elev:#fff;--separator:rgba(60,60,67,.12);--separator-strong:rgba(60,60,67,.24);
--text:#000;--text-secondary:rgba(30,30,40,.86);--text-tertiary:rgba(60,60,67,.3);--fill:rgba(120,120,128,.16);
--glass-tint:255,255,255;--glass-tint-dark:255,255,255;
--gloss:226,234,248;--gloss-border:.5;--gloss-hi:.45;--gloss-hi-sm:.34;--glass-inner:rgba(0,0,0,.04);--glass-drop:rgba(0,0,0,.12);--glass-drop-sm:rgba(0,0,0,.09);
}


*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%}
body{font-family:var(--font);background:var(--bg);color:var(--text);overflow:hidden;position:fixed;inset:0;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;font-variant-numeric:tabular-nums}
button{font-family:inherit;color:inherit;background:none;border:none;cursor:pointer}
button:focus-visible,input:focus-visible,textarea:focus-visible,summary:focus-visible{outline:2px solid var(--blue);outline-offset:2px}
::selection{background:color-mix(in srgb,var(--blue) 30%,transparent)}

#wallpaper{position:fixed;inset:-10%;z-index:0;filter:saturate(140%);opacity:.85;pointer-events:none;transition:opacity 500ms var(--ease-out),filter 600ms var(--ease-out)}
body.page-hidden #wallpaper{visibility:hidden}
.blob{position:absolute;border-radius:50%;mix-blend-mode:screen;animation:drift 26s ease-in-out infinite alternate}
.b1{width:55vw;height:55vw;left:-10vw;top:-10vh;background:radial-gradient(circle,var(--blue),transparent 70%)}
.b2{width:50vw;height:50vw;right:-8vw;top:5vh;background:radial-gradient(circle,var(--purple),transparent 70%);animation-delay:-6s}
.b3{width:48vw;height:48vw;left:20vw;bottom:-12vh;background:radial-gradient(circle,var(--teal),transparent 70%);animation-delay:-12s}
.b4{width:40vw;height:40vw;right:10vw;bottom:-8vh;background:radial-gradient(circle,var(--blob4,var(--orange)),transparent 70%);animation-delay:-18s}
.b5{width:34vw;height:34vw;left:38vw;top:30vh;background:radial-gradient(circle,var(--blob5,var(--pink)),transparent 70%);animation-delay:-9s}
@keyframes drift{0%{transform:translate(0,0) scale(1)}50%{transform:translate(4vw,-3vh) scale(1.12)}100%{transform:translate(-3vw,4vh) scale(.95)}}

#app{position:relative;z-index:1;height:100%;display:flex;flex-direction:column;transition:opacity 220ms var(--ease-out)}

.glass{
background:rgba(var(--glass-tint-dark),var(--glass-opacity));
-webkit-backdrop-filter:blur(var(--glass-blur)) saturate(var(--glass-saturate));backdrop-filter:blur(var(--glass-blur)) saturate(var(--glass-saturate));
border:.5px solid rgba(var(--gloss),calc(var(--gloss-border) * var(--glass-specular)));
box-shadow:inset 0 1px 1px rgba(var(--gloss),calc(var(--gloss-hi) * var(--glass-specular))),inset 0 -1px 2px var(--glass-inner),0 12px 40px var(--glass-drop);
transition:background-color 260ms var(--ease-out),box-shadow 260ms var(--ease-out),border-color 260ms var(--ease-out);
}

#top{position:relative;z-index:5;flex:none;pointer-events:none}
#top button,#top input,#chips .chip,#searchbar,#warnBar,#titlebar,.header-title-wrap{pointer-events:auto}
#header{position:relative;padding:14px 20px 10px;transition:transform var(--dur) var(--ease-out),opacity 200ms var(--ease-out),visibility 0s}
.header-top{display:flex;align-items:center;justify-content:space-between;gap:12px;position:relative;z-index:1}
.header-title-wrap{display:flex;flex-direction:column;min-width:0}
.header-title{font-size:2.125rem;font-weight:700;letter-spacing:-.022em;line-height:1.1;line-height:round(up,1.1em,1px);transform-origin:left center;transition:transform var(--dur) var(--ease-out),opacity 200ms var(--ease-out);white-space:nowrap}
body:not(.searching) #header.scrolled{transform:translateY(-100%);opacity:0;visibility:hidden;transition-delay:0s,0s,.25s}
#chips{transition:transform var(--dur) var(--ease-out)}
body:not(.searching) #top.scrolled #chips{transform:translateY(calc(var(--hdrH,0px) * -1))}
.header-subtitle{line-height:1.3;line-height:round(up,1.3em,1px);font-size:0.8125rem;color:var(--text-secondary);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:opacity 200ms var(--ease-out)}
.header-actions{display:flex;gap:8px;flex-shrink:0}
.icon-btn{position:relative;width:38px;height:38px;border-radius:50%;display:grid;place-items:center;transition:transform 120ms var(--ease-out)}
.icon-btn::before{content:"";position:absolute;inset:-3px;border-radius:50%}
.icon-btn:active{transform:scale(.88)}
.icon-btn svg{width:20px;height:20px}
.sync-spin{animation:spin .9s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

#scroll{flex:1;overflow-y:auto;overflow-x:hidden;margin-top:calc(var(--topH,0px) * -1);padding:calc(6px + var(--topH,0px)) 16px 120px;scroll-padding-top:var(--topH,0px);scroll-behavior:smooth}
#scroll::-webkit-scrollbar{width:8px}
#scroll::-webkit-scrollbar-thumb{background:var(--fill);border-radius:8px}
#scroll::-webkit-scrollbar-track{background:transparent}

#chips{display:flex;gap:8px;overflow-x:auto;padding:4px 20px 12px;scrollbar-width:none}
#chips:empty{display:none}
#chips::-webkit-scrollbar{display:none}
.chip.type-filter{display:inline-flex;align-items:center;gap:10px;max-width:260px}
.type-filter span{overflow:hidden;text-overflow:ellipsis}
.type-filter svg{width:14px;height:14px;flex-shrink:0}
.type-menu.glass{position:fixed;z-index:26;padding:6px;border-radius:20px;overflow-y:auto;overscroll-behavior:contain;scrollbar-width:thin;visibility:hidden;pointer-events:none;opacity:0;transform:translateY(-6px) scale(.97);transform-origin:top left;transition:opacity 160ms var(--ease-out),transform 200ms var(--ease-out),visibility 0s 200ms}
.type-menu.open{visibility:visible;pointer-events:auto;opacity:1;transform:translateY(0) scale(1);transition-delay:0s}
.type-menu-option{display:flex;align-items:center;justify-content:space-between;gap:16px;width:100%;padding:11px 12px;border-radius:14px;text-align:left;font-size:.875rem;overflow-wrap:anywhere;opacity:0;transform:translateY(-4px);transition:opacity 160ms var(--ease-out),transform 180ms var(--ease-out)}
.type-menu.open .type-menu-option{opacity:1;transform:translateY(0);transition-delay:var(--item-delay,0ms)}
.type-menu-option[aria-selected="true"]{background:color-mix(in srgb,var(--blue) 16%,transparent);font-weight:600}
.type-menu-option svg{width:16px;height:16px;flex-shrink:0;color:var(--blue)}
.type-menu-option:focus-visible{outline:2px solid var(--blue);outline-offset:-2px;background:var(--fill)}
@media(hover:hover) and (pointer:fine){.type-menu-option:hover{background:var(--fill)}}
[data-rendering="performance"] .type-menu,.type-menu.instant{transition:none;transform:none}
[data-rendering="performance"] .type-menu .type-menu-option,.type-menu.instant .type-menu-option{transition:none;transform:none}
@media(prefers-reduced-motion:reduce){.type-menu.glass,.type-menu .type-menu-option{transition:none;transform:none}}
.lvs-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:0 8px 18px}
.lvs-toolbar .header-subtitle{margin:0}
.lvs-toolbar button:disabled{opacity:.5;cursor:default}
.grade-row.lvs-item{position:relative;width:100%;text-align:left;padding-right:26px}
.unread-dot{position:absolute;top:8px;right:8px;width:7px;height:7px;border-radius:50%;background:#ff453a;pointer-events:none}
.chip{position:relative;flex-shrink:0;padding:10px 16px;border-radius:var(--radius-chip);font-size:0.875rem;font-weight:500;color:var(--text);background:rgba(var(--glass-tint-dark),.5);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);border:.5px solid rgba(255,255,255,.12);transition:transform 120ms var(--ease-out),background 200ms,color 200ms;white-space:nowrap}
.chip:active{transform:scale(.94)}
.chip::before{content:"";position:absolute;inset:-3px 0}
.chip.active{background:color-mix(in srgb,var(--blue) 80%,#000);color:#fff;border-color:transparent}

.section{margin-bottom:26px}
.section-header{font-size:1.375rem;font-weight:700;letter-spacing:-.02em;padding:6px 8px 10px;display:flex;align-items:baseline;justify-content:space-between}
.section-header .count{font-size:0.875rem;font-weight:500;color:var(--text-secondary)}
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
.completed-toggle{width:100%;display:flex;align-items:center;justify-content:space-between;padding:6px 8px 10px;font-size:1.375rem;font-weight:700;letter-spacing:-.02em;text-align:left}
.completed-toggle .meta{display:flex;align-items:center;gap:8px;font-size:0.875rem;font-weight:500;color:var(--text-secondary)}
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
.task-course{font-size:0.9375rem;font-weight:600}
.task-desc{font-size:0.9375rem;line-height:1.35;margin-top:2px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.task-info{font-size:0.8125rem;letter-spacing:.005em;line-height:1.35;color:var(--text-secondary);margin-top:4px;display:-webkit-box;-webkit-line-clamp:2;line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;white-space:pre-line}
.detail-info{font-size:1rem;line-height:1.45;white-space:pre-wrap;padding:14px;border-radius:var(--radius-row);background:color-mix(in srgb,var(--text) 5%,transparent)}
.release-notes{font-size:1rem;line-height:1.45;overflow-wrap:anywhere}
.release-notes p,.release-notes ul{margin-bottom:12px}
.release-notes ul{padding-left:22px}
.release-notes h4{margin-top:16px}
.today-tag{font-size:0.75rem;font-weight:600;padding:2px 8px;border-radius:999px;margin-left:8px;vertical-align:middle;background:color-mix(in srgb,var(--blue) 22%,transparent);color:var(--blue)}
.task-row .task-body{padding-right:26px}
.task-pin{position:absolute;top:10px;right:10px;width:30px;height:30px;border-radius:50%;display:grid;place-items:center;color:var(--text-tertiary);opacity:0;transition:opacity 150ms,color 150ms,transform 120ms}
.task-pin::before{content:"";position:absolute;inset:-7px}
.task-pin svg{width:16px;height:16px}
.task-row:hover .task-pin,.task-pin.on,.task-pin:focus-visible{opacity:1}
.task-pin.on{color:var(--orange)}
.task-pin.on svg{fill:currentColor}
.task-pin:active{transform:scale(.85)}
.task-row-actions{display:flex;align-items:center;gap:8px;flex-shrink:0}
.task-row-actions .task-pin{position:relative;top:auto;right:auto}
.task-focus{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;color:var(--text-tertiary);opacity:0;transition:opacity 150ms,color 150ms,transform 120ms}
.task-focus svg{width:16px;height:16px}
.task-row:hover .task-focus,.task-row:focus-within .task-focus,.task-focus:focus-visible{opacity:1}
.task-focus:hover{color:var(--text)}
@media (hover:none){.task-focus,.task-pin{opacity:1}}
.task-focus:active{transform:scale(.95)}
.task-note{font-size:0.8125rem;line-height:1.35;color:var(--orange);margin-top:4px;font-style:italic;display:-webkit-box;-webkit-line-clamp:1;line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}
.task-meta svg.mini{width:13px;height:13px;vertical-align:-2px;margin-right:2px}
#searchbar{display:none;padding:2px 20px 10px;position:relative;z-index:4}
body.searching #searchbar{display:block}
#searchInput{width:100%;box-sizing:border-box;border:0;outline:none;border-radius:999px;padding:11px 42px 11px 18px;font:inherit;font-size:0.9375rem;color:var(--text);background:var(--fill);-webkit-backdrop-filter:blur(var(--glass-blur));backdrop-filter:blur(var(--glass-blur))}
#searchInput::placeholder{color:var(--text-secondary)}
#searchClear{position:absolute;right:30px;top:50%;transform:translateY(-62%);width:26px;height:26px;border-radius:50%;display:grid;place-items:center;color:var(--text-secondary)}
.overview{padding:16px 18px 14px}
.overview .summary-text{font-size:0.9375rem;line-height:1.45;white-space:pre-line}
.busy{display:flex;gap:8px;align-items:flex-end;height:92px;margin-top:14px}
.busy-col{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:4px;height:100%}
.busy-bar{width:100%;max-width:36px;border-radius:9px 9px 4px 4px;background:var(--blue);min-height:4px;transition:height 300ms var(--ease-out)}
.busy-col.mid .busy-bar{background:var(--orange)}
.busy-col.high .busy-bar{background:var(--red)}
.busy-col.zero .busy-bar{background:var(--fill)}
.busy-n{font-size:0.75rem;font-weight:600;color:var(--text)}
.busy-col.zero .busy-n{color:var(--text-secondary)}
.busy-day{font-size:0.75rem;color:var(--text)}
.busy-col.today .busy-day{font-weight:700;color:var(--text)}
.busy-legend{font-size:0.75rem;color:var(--text-secondary);margin-top:8px}
.chip-link{display:inline-flex;align-items:center;gap:6px;max-width:100%;padding:8px 13px;border-radius:999px;background:var(--fill);font-size:0.875rem;margin:0 8px 8px 0;cursor:pointer;word-break:break-word}
.chip-link.static{cursor:default}
.chip-link svg{width:15px;height:15px;flex-shrink:0}
.note-area{width:100%;box-sizing:border-box;min-height:110px;resize:vertical;border:0;outline:none;border-radius:var(--radius-row);padding:12px 14px;font:inherit;font-size:0.9375rem;line-height:1.4;color:var(--text);background:color-mix(in srgb,var(--text) 6%,transparent)}
.btn-secondary{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:13px;border-radius:var(--radius-row);font-size:0.9375rem;font-weight:600;background:var(--fill);color:var(--text);margin-bottom:10px}
.btn-secondary svg{width:16px;height:16px}
.task-actions{display:flex;align-items:stretch;gap:10px;margin-bottom:14px}
.task-actions .btn-secondary{width:auto;margin:0;padding:10px 14px;font-size:.875rem}
.task-actions [data-pin-sheet]{flex:1;min-width:0}
.task-actions [data-focus-task]{flex-shrink:0}
.grade-row{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:13px 16px;position:relative;cursor:pointer}
.grade-row+.grade-row::before{content:"";position:absolute;left:16px;right:0;top:0;height:.5px;background:var(--separator)}
.grade-name{font-weight:500;font-size:0.9375rem}
.grade-meta{font-size:0.8125rem;color:var(--text-secondary);margin-top:2px}
.grade-score{font-size:1.0625rem;font-weight:700;text-align:right;white-space:nowrap}
.grade-pct{font-size:0.75rem;color:var(--text-secondary);font-weight:500;text-align:right}
.grade-square{display:inline-block;width:26px;height:26px;border-radius:8px;vertical-align:middle;box-shadow:inset 0 0 0 1px rgba(255,255,255,.4),0 1px 4px rgba(0,0,0,.22)}
.avg-pill{display:inline-block;margin-left:8px;padding:2px 9px;border-radius:999px;font-size:0.75rem;font-weight:700;vertical-align:middle;background:var(--fill)}
.grade-summary{padding:16px 18px;display:flex;align-items:baseline;justify-content:space-between;gap:12px}
.grade-summary b{font-size:1.75rem;letter-spacing:-.02em}
.task-meta{font-size:0.8125rem;color:var(--text-secondary);margin-top:6px;display:flex;gap:10px;flex-wrap:wrap;align-items:center}

.badge{display:inline-flex;align-items:center;gap:4px;font-size:0.75rem;font-weight:600;padding:3px 8px;border-radius:999px;letter-spacing:.02em}
.badge svg{width:13px;height:13px}
.badge-type{background:var(--fill);color:var(--text)}
.badge-type.toets{background:color-mix(in srgb,var(--red) 20%,transparent);color:color-mix(in srgb,var(--red) 25%,var(--text))}
.badge-type.taak{background:color-mix(in srgb,var(--blue) 20%,transparent);color:color-mix(in srgb,var(--blue) 25%,var(--text))}
.badge-type.opdracht{background:color-mix(in srgb,var(--purple) 20%,transparent);color:color-mix(in srgb,var(--purple) 25%,var(--text))}
.badge-corrected{background:color-mix(in srgb,var(--orange) 20%,transparent);color:var(--orange)}
.badge-ai{background:color-mix(in srgb,var(--purple) 20%,transparent);color:var(--purple)}
.badge-warn{background:color-mix(in srgb,var(--red) 20%,transparent);color:var(--red)}

.lesson-row{display:flex;gap:12px;padding:14px 16px;position:relative;cursor:pointer;transition:background 200ms}
.lesson-row+.lesson-row::before{content:"";position:absolute;left:78px;right:0;top:0;height:.5px;background:var(--separator)}
.lesson-time{flex-shrink:0;width:62px;font-size:0.8125rem;font-weight:600;color:var(--text-secondary);padding-top:2px}
.lesson-time .end{display:block;color:var(--text-secondary);font-weight:500;font-size:0.75rem}
.lesson-bar{width:4px;border-radius:4px;flex-shrink:0;align-self:stretch;background:var(--blue)}
.lesson-bar.frans{background:var(--purple)}.lesson-bar.geschiedenis{background:var(--orange)}.lesson-bar.nederlands{background:var(--green)}
.lesson-bar.english,.lesson-bar.engels{background:var(--teal)}
.lesson-body{min-width:0;flex:1}
.lesson-title{font-size:0.9375rem;font-weight:600}
.lesson-sub{font-size:0.8125rem;letter-spacing:.005em;color:var(--text-secondary);margin-top:2px}
.lesson-assign{margin-top:8px;padding:8px 10px;border-radius:12px;background:color-mix(in srgb,var(--blue) 12%,transparent);font-size:0.8125rem;display:flex;gap:8px;align-items:flex-start}
.lesson-assign .check{width:20px;height:20px;margin-top:0;border-width:1.5px}
.lesson-assign .check.done::after{width:9px;height:5px}
.lesson-assign .check.done{border-width:0}

.empty{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 30px;text-align:center;gap:14px}
.empty svg{width:64px;height:64px;opacity:.5;color:var(--text-secondary)}
.empty h3{font-size:1.25rem;font-weight:700}
.empty p{font-size:0.9375rem;color:var(--text-secondary);max-width:280px;line-height:1.4}

#tabbar{position:fixed;left:0;right:0;margin-inline:auto;bottom:18px;z-index:20}.app-bar{position:relative;display:flex;border-radius:var(--radius-chip);padding:8px 10px;gap:0;width:min(560px,calc(100% - 32px));justify-content:space-around}
.app-bar .bubble{position:absolute;top:8px;bottom:8px;left:10px;width:calc((100% - 20px) / var(--tab-count));border-radius:var(--radius-chip);background:rgba(255,255,255,.14);border:.5px solid rgba(255,255,255,.2);transition:transform 360ms var(--ease-out);z-index:0;box-shadow:inset 0 1px 1px rgba(255,255,255,.25)}
[data-scheme="light"] .app-bar .bubble{background:rgba(60,90,140,.07);border-color:rgba(255,255,255,.6)}
.tab,.focus-action{position:relative;z-index:1;flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;padding:8px 4px;border-radius:var(--radius-chip);font-size:0.75rem;font-weight:500;letter-spacing:.02em;color:var(--text-secondary);transition:color 200ms,transform 120ms;min-width:0}
.tab:active,.focus-action:active{transform:scale(.92)}
.tab.active{color:var(--text)}
.tab svg,.focus-action svg{width:24px;height:24px}
.tab-badge{position:absolute;top:2px;right:calc(50% - 22px);min-width:20px;height:20px;padding:0 4px;line-height:1;border-radius:999px;background:var(--red);color:#fff;font-size:0.75rem;font-weight:700;display:grid;place-items:center;border:2px solid var(--bg)}

#sheet-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:30;opacity:0;pointer-events:none;transition:opacity 280ms var(--ease-out)}
#sheet-backdrop.show{opacity:1;pointer-events:auto}
#sheet{position:fixed;left:0;right:0;margin-inline:auto;bottom:0;transform:translate(0,100%);width:min(560px,100%);max-height:86vh;z-index:31;border-radius:var(--radius-sheet) var(--radius-sheet) 0 0;padding:0 0 24px;overflow:hidden;transition:transform 300ms var(--ease-out);display:flex;flex-direction:column}
#sheet.show{transform:translate(0,0)}
.sheet-grabber{width:40px;height:5px;border-radius:3px;background:var(--text-tertiary);margin:9px auto 6px;flex-shrink:0}
.sheet-head{padding:4px 20px 12px;display:flex;justify-content:space-between;align-items:center;flex-shrink:0;position:relative;z-index:1}
.sheet-head h2{font-size:1.375rem;font-weight:700;letter-spacing:-.02em}
.sheet-close{width:32px;height:32px;border-radius:50%;background:var(--fill);display:grid;place-items:center;transition:transform 120ms}
.sheet-close:active{transform:scale(.85)}
.sheet-scroll{overflow-y:auto;padding:0 20px 20px;position:relative;z-index:1}
.sheet-scroll::-webkit-scrollbar{width:6px}
.sheet-scroll::-webkit-scrollbar-thumb{background:var(--fill);border-radius:6px}

.detail-block{margin-bottom:18px}
.detail-block h4,.setting-group h4{font-size:0.8125rem;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.04em;margin-bottom:8px}
.detail-desc{font-size:1.0625rem;line-height:1.4;font-weight:500}
.detail-list{border-radius:var(--radius-row);overflow:hidden;background:color-mix(in srgb,var(--text) 5%,transparent)}
.detail-row{display:flex;justify-content:space-between;gap:16px;padding:13px 14px;font-size:0.9375rem;position:relative}
.detail-row+.detail-row::before{content:"";position:absolute;left:14px;right:0;top:0;height:.5px;background:var(--separator)}
.detail-row .k{color:var(--text-secondary)}
.detail-row .v{text-align:right;font-weight:500;max-width:60%}
.detail-badges{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 10px}
.btn-primary{width:100%;padding:14px;border-radius:16px;background:var(--blue);color:#fff;font-size:1.0625rem;font-weight:600;display:flex;align-items:center;justify-content:center;gap:8px;transition:transform 120ms}
.btn-primary:active{transform:scale(.97)}
.btn-primary svg{width:18px;height:18px}

.setting-group{margin-bottom:18px}
.setting-row{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;font-size:1rem}
.seg-control{display:flex;padding:4px;gap:4px}
.seg{flex:1;padding:10px;border-radius:12px;font-size:0.9375rem;font-weight:600;color:var(--text-secondary);transition:background 200ms,color 200ms,transform 120ms}
.seg:active{transform:scale(.96)}
.seg.active{background:var(--blue);color:#fff}
.glass-slider{width:100%;-webkit-appearance:none;appearance:none;height:32px;background:transparent;margin:6px 0}
.glass-slider::-webkit-slider-runnable-track{height:6px;border-radius:3px;background:linear-gradient(90deg,var(--teal),var(--blue),var(--purple))}
.glass-slider::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:28px;height:28px;border-radius:50%;background:#fff;margin-top:-11px;box-shadow:0 2px 8px rgba(0,0,0,.4),inset 0 0 0 1px rgba(0,0,0,.1);cursor:pointer}
.glass-level-labels{display:flex;justify-content:space-between;font-size:0.75rem;color:var(--text-secondary);padding:0 4px}
.toggle{width:51px;height:31px;border-radius:999px;background:var(--fill);position:relative;transition:background 200ms;flex-shrink:0;cursor:pointer}
.toggle.on{background:var(--green)}
.toggle::after{content:"";position:absolute;top:2px;left:2px;width:27px;height:27px;border-radius:50%;background:#fff;transition:transform 220ms var(--ease-spring);box-shadow:0 2px 5px rgba(0,0,0,.3)}
.toggle.on::after{transform:translateX(20px)}

#state-overlay{position:fixed;inset:0;z-index:40;display:none;flex-direction:column;align-items:center;justify-content:center;padding:40px;background:rgba(var(--glass-tint-dark),.78);-webkit-backdrop-filter:blur(24px);backdrop-filter:blur(24px)}
#state-overlay.show{display:flex}
#stateContent{display:flex;flex-direction:column;align-items:center;gap:20px;width:100%}
.state-spinner{width:44px;height:44px;border-radius:50%;border:4px solid var(--text-tertiary);border-top-color:var(--blue);animation:spin .9s linear infinite}
.skeleton-group{width:min(420px,90%)}
.skel{border-radius:var(--radius-card);height:78px;margin-bottom:14px;background:linear-gradient(100deg,rgba(255,255,255,.06) 30%,rgba(255,255,255,.14) 50%,rgba(255,255,255,.06) 70%);background-size:200% 100%;animation:shimmer 1.4s infinite}
@keyframes shimmer{to{background-position:-200% 0}}
.error-icon{width:64px;height:64px;color:var(--red)}
.error-icon svg{width:100%;height:100%}
.error-title{font-size:1.375rem;font-weight:700}
.error-msg{font-size:0.9375rem;color:var(--text-secondary);text-align:center;max-width:320px;line-height:1.4}
.retry-btn{padding:13px 28px;border-radius:999px;background:var(--blue);color:#fff;font-size:1rem;font-weight:600;display:flex;align-items:center;gap:8px;transition:transform 120ms}
.retry-btn:active{transform:scale(.96)}
.retry-btn svg{width:18px;height:18px}
.error-hint{font-size:0.875rem;color:var(--text-secondary);text-align:center;max-width:340px;line-height:1.4;opacity:.9}
.error-actions{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin-top:4px}
.error-actions .retry-btn{margin:0}
.retry-btn.secondary{background:rgba(var(--glass-tint-dark),.55);color:var(--text);border:1px solid rgba(128,128,128,.35)}
.error-details{max-width:360px;width:100%;font-size:0.75rem;color:var(--text-secondary)}
.error-details summary{cursor:pointer;text-align:center;opacity:.8}
.error-details pre{margin-top:8px;max-height:140px;overflow:auto;white-space:pre-wrap;word-break:break-word;text-align:left;padding:10px;border-radius:10px;background:rgba(128,128,128,.15);font-size:0.75rem;user-select:text}
#warnBar{display:none;margin:0 16px 8px;padding:12px 14px;border-radius:16px;border:1px solid rgba(255,159,10,.45);background:rgba(255,159,10,.14);box-shadow:inset 0 0 0 999px rgba(var(--glass-tint-dark),.55);-webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px);font-size:0.8438rem;line-height:1.4;gap:10px;align-items:flex-start}
#warnBar.show{display:flex}
#warnBar .warn-ico{width:20px;height:20px;flex:none;color:#ff9f0a;margin-top:1px}
#warnBar .warn-ico svg{width:100%;height:100%}
#warnBar .warn-body{flex:1;min-width:0}
#warnBar .warn-title{font-weight:700}
#warnBar .warn-hint{opacity:.8;margin-top:2px}
#warnBar .warn-btns{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}
#warnBar button{padding:6px 12px;border-radius:999px;font-size:0.8125rem;font-weight:600;background:rgba(128,128,128,.22);color:inherit}
#warnBar .warn-x{flex:none;padding:2px 8px;font-size:1.125rem;line-height:1;background:transparent;opacity:.6}

.detail-block details.raw summary{cursor:pointer;font-size:0.8125rem;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.04em;padding:4px 0 8px;list-style:none}
details.raw summary::-webkit-details-marker{display:none}
details.raw summary::before{content:"\25B8  "}
details.raw[open] summary::before{content:"\25BE  "}
details.raw .detail-row .k{font-size:0.75rem;word-break:break-word;max-width:42%}
details.raw .detail-row .v{font-size:0.8125rem;word-break:break-word}
/* frameless window */
:root{__WC_VARS__}
#titlebar{display:none;flex:0 0 36px;height:36px;position:relative;z-index:6;user-select:none;-webkit-user-select:none}
body.framed #titlebar{display:block}
body.framed #header{padding-top:0}
#wc{position:fixed;top:9px;right:14px;z-index:50;display:none;gap:8px}
body.framed #wc{display:flex}
.wc-btn{position:relative;width:18px;height:18px;padding:0;margin:0;border:0;border-radius:50%;background-color:transparent;background-size:contain;background-repeat:no-repeat;background-position:center;cursor:default;outline:none}
#wcClose{background-image:var(--wc-close)} #wcClose:hover{background-image:var(--wc-close-hover)}
#wcMin{background-image:var(--wc-min)} #wcMin:hover{background-image:var(--wc-min-hover)}
#wcMax{background-image:var(--wc-max)} #wcMax:hover{background-image:var(--wc-max-hover)}
.wc-btn::before{content:"";position:absolute;inset:-5px}
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
@media (prefers-reduced-motion:reduce){.blob,.skel{animation:none}#scroll{scroll-behavior:auto}*{transition-duration:.01ms !important}#sheet{transition:opacity 200ms linear !important;transform:translate(0,0) !important;opacity:0;pointer-events:none}#sheet.show{opacity:1;pointer-events:auto}}
@media (prefers-reduced-transparency:reduce){.glass,.group{-webkit-backdrop-filter:none !important;backdrop-filter:none !important;background:var(--bg-elev) !important}.blob{display:none}}
@media (prefers-contrast:more){:root{--text-secondary:var(--text);--separator:var(--separator-strong)}.glass,.group{border-width:1px;border-color:var(--text-secondary)}}
body.reduce-motion *{animation-duration:.01ms !important;transition-duration:.01ms !important}
body.reduce-motion .blob{animation:none}

/* CLEAR: cool snow palette, near-transparent glass, sharp specular rim */
[data-style="clear"]{--blue:#6FB6F2;--orange:#E0B87A;--purple:#A9A4DD;--red:#F0908F;--green:#8ED1A8;--yellow:#E8D68C;--teal:#7FD6EC;--pink:#BFC9DA;--blob4:#6F9BCB;--blob5:#A9BFDD;--bg:#0A1119;--bg-elev:#152031;--text:#F4F8FD;--text-secondary:rgba(236,243,252,.86);--text-tertiary:rgba(228,238,250,.42);--separator:rgba(220,235,255,.12);--separator-strong:rgba(220,235,255,.24);--fill:rgba(170,200,235,.2);--gloss:190,212,240;--gloss-border:.3;--gloss-hi:.3;--gloss-hi-sm:.22;--glass-inner:rgba(200,225,255,.03);--glass-drop:rgba(0,8,20,.32);--glass-drop-sm:rgba(0,8,20,.24)}
:root[data-scheme="light"][data-style="clear"]{--blue:#2F76B8;--orange:#BC6608;--purple:#5B58A8;--red:#C0392F;--green:#277A4C;--yellow:#86710F;--teal:#1A7897;--pink:#5F7391;--blob4:#CFE6FA;--blob5:#FFFFFF;--bg:#EDF3FA;--bg-elev:#fff;--text:#0B1626;--text-secondary:rgba(18,36,60,.76);--text-tertiary:rgba(18,36,60,.42);--separator:rgba(40,70,110,.14);--separator-strong:rgba(40,70,110,.26);--fill:rgba(60,100,150,.12);--gloss:196,216,244;--gloss-border:.6;--gloss-hi:.5;--gloss-hi-sm:.4;--glass-inner:rgba(80,110,150,.05);--glass-drop:rgba(40,70,110,.09);--glass-drop-sm:rgba(40,70,110,.07)}
[data-style="clear"] #wallpaper{opacity:.78}
:root[data-scheme="light"][data-style="clear"] #wallpaper{opacity:.7}
[data-style="clear"] .blob{animation-duration:40s}
[data-style="clear"] .header-title,[data-style="clear"] .header-subtitle,[data-style="clear"] .section-header{text-shadow:0 1px 2px rgba(0,8,20,.35)}
:root[data-scheme="light"][data-style="clear"] .header-title,:root[data-scheme="light"][data-style="clear"] .header-subtitle,:root[data-scheme="light"][data-style="clear"] .section-header{text-shadow:none}
body.static-bg .blob{animation:none}
body.resizing .blob{animation-play-state:paused}
.blob{filter:blur(70px)}
body.inactive .blob{animation-play-state:paused}
#scroll,.sheet-scroll,#sheetBody{overscroll-behavior:contain}
.tab,.chip,.icon-btn,.seg,.btn-primary,.btn-secondary,.sheet-close,.toggle,.check,.sheet-head{user-select:none;-webkit-user-select:none}
.sheet-head,.sheet-grabber{touch-action:none;cursor:grab}
.sheet-close{cursor:pointer}
.sheet-grabber{position:relative}
.sheet-grabber::before{content:"";position:absolute;inset:-10px -40px}
#sheet:focus{outline:none}
.task-body:focus-visible,.lesson-body:focus-visible,.grade-row:focus-visible,.check:focus-visible,.toggle:focus-visible{outline:2px solid var(--blue);outline-offset:2px;border-radius:8px}
#toast{position:fixed;left:0;right:0;margin-inline:auto;width:max-content;max-width:calc(100% - 32px);bottom:104px;transform:translate(0,12px);z-index:25;display:flex;align-items:center;gap:12px;padding:8px 8px 8px 18px;border-radius:999px;background:var(--bg-elev);border:.5px solid var(--separator-strong);box-shadow:0 8px 24px var(--glass-drop-sm);font-size:0.875rem;font-weight:500;opacity:0;pointer-events:none;transition:opacity 200ms var(--ease-out),transform 260ms var(--ease-out)}
#toast.show{opacity:1;transform:translate(0,0);pointer-events:auto}
#toast button{min-height:40px;padding:0 16px;border-radius:999px;font-weight:600;color:var(--text);background:var(--fill)}
@keyframes tabin{from{transform:translateX(var(--dx,14px))}}
#scroll.tab-in{animation:tabin 280ms var(--ease-out)}
@media (prefers-reduced-motion:reduce){#scroll.tab-in{animation:none}}
body.reduce-motion #scroll.tab-in{animation:none}
@media (hover:hover){
.task-row:hover,.lesson-row:hover,.grade-row:hover{box-shadow:inset 0 0 0 999px color-mix(in srgb,var(--text) 4%,transparent)}
.chip:not(.active):hover{background:color-mix(in srgb,var(--text) 14%,transparent)}
.tab:not(.active):hover{color:var(--text)}
.icon-btn:hover{transform:scale(1.06)}
.icon-btn:active{transform:scale(.88)}
.seg:not(.active):hover,.btn-secondary:hover,.sheet-close:hover,#toast button:hover{background:color-mix(in srgb,var(--text) 14%,transparent)}
}
.app-bar{touch-action:none;background-color:rgba(var(--glass-tint-dark),calc(var(--glass-opacity) + .1))}
[data-style="clear"] .chip.active{background:var(--blue);color:#04101c}
:root[data-scheme="light"][data-style="clear"] .chip.active{background:color-mix(in srgb,var(--blue) 82%,#000);color:#fff}
.no-trans,.no-trans *,.no-trans *::before,.no-trans *::after{transition:none !important}
html[data-text="s"]{font-size:90%}
html[data-text="l"]{font-size:115%}
.app-bar.scrubbing .bubble{transition:none}
.app-bar.scrubbing .tab{transition:color 120ms}
.tab.peek{color:var(--text)}
.empty .retry-btn{margin-top:6px}
.busy-col{position:relative}
.busy-col::after,.icon-btn::after{content:attr(data-tip);position:absolute;white-space:nowrap;padding:6px 10px;border-radius:10px;background:var(--bg-elev);color:var(--text);font-size:.75rem;font-weight:500;box-shadow:0 6px 18px var(--glass-drop-sm);opacity:0;pointer-events:none;transition:opacity 150ms;z-index:30}
.busy-col::after{bottom:calc(100% + 6px);left:50%;transform:translateX(-50%)}
.icon-btn::after{content:attr(aria-label);top:calc(100% + 8px);right:0}
.busy-col:hover::after,.busy-col:focus-visible::after,.icon-btn:focus-visible::after{opacity:1}
.busy-col:focus-visible{outline:2px solid var(--blue);outline-offset:2px;border-radius:8px}

/* ===== LIQUID GLASS LIGHTING: directional specular edges, sheen, rim ring ===== */
.glass,.group,.chip,.icon-btn{background-image:linear-gradient(155deg,rgba(255,255,255,.20) 0%,rgba(255,255,255,0) 36%,rgba(255,255,255,0) 68%,rgba(255,255,255,.07) 100%)}
.glass{box-shadow:inset 2px 2px 2px -2px rgba(var(--gloss),calc(var(--gloss-hi) * 1 * var(--glass-specular))),inset 6px 6px 12px -8px rgba(var(--gloss),calc(var(--gloss-hi) * 0.5 * var(--glass-specular))),inset -2px -2px 2px -2px rgba(var(--gloss),calc(var(--gloss-hi) * 0.45 * var(--glass-specular))),inset -6px -6px 12px -8px rgba(var(--gloss),calc(var(--gloss-hi) * 0.2 * var(--glass-specular))),inset 0 0 22px rgba(var(--gloss),.07),inset 0 -2px 5px -2px var(--glass-inner),0 12px 40px var(--glass-drop)}
.group{box-shadow:inset 2px 2px 2px -2px rgba(var(--gloss),calc(var(--gloss-hi-sm) * 1 * var(--glass-specular))),inset 6px 6px 12px -8px rgba(var(--gloss),calc(var(--gloss-hi-sm) * 0.5 * var(--glass-specular))),inset -2px -2px 2px -2px rgba(var(--gloss),calc(var(--gloss-hi-sm) * 0.45 * var(--glass-specular))),inset -6px -6px 12px -8px rgba(var(--gloss),calc(var(--gloss-hi-sm) * 0.2 * var(--glass-specular))),inset 0 0 18px rgba(var(--gloss),.06),0 8px 30px var(--glass-drop-sm)}
.chip,.icon-btn{box-shadow:inset 2px 2px 2px -2px rgba(255,255,255,0.7),inset 6px 6px 12px -8px rgba(255,255,255,0.315),inset -2px -2px 2px -2px rgba(255,255,255,0.32),inset -6px -6px 12px -8px rgba(255,255,255,0.112),0 4px 14px rgba(0,0,0,.08)}
.chip.active{background-image:none;box-shadow:inset 2px 2px 2px -2px rgba(255,255,255,0.55),inset 6px 6px 12px -8px rgba(255,255,255,0.248),0 4px 14px rgba(0,0,0,.14)}
.app-bar .bubble{box-shadow:inset 2px 2px 2px -2px rgba(255,255,255,0.85),inset 6px 6px 12px -8px rgba(255,255,255,0.383),inset -2px -2px 2px -2px rgba(255,255,255,0.4),inset -6px -6px 12px -8px rgba(255,255,255,0.14),inset 0 0 14px rgba(255,255,255,.1),0 2px 10px rgba(0,0,0,.12)}
[data-scheme="light"] .app-bar .bubble{background-image:linear-gradient(155deg,rgba(255,255,255,.16) 0%,rgba(255,255,255,0) 45%,rgba(255,255,255,0) 100%);box-shadow:inset 2px 2px 2px -2px rgba(255,255,255,0.95),inset 6px 6px 12px -8px rgba(255,255,255,0.427),inset -2px -2px 2px -2px rgba(255,255,255,0.55),inset -6px -6px 12px -8px rgba(255,255,255,0.193),inset 0 -4px 10px -4px rgba(30,50,90,.12),inset 0 0 14px rgba(255,255,255,.06),0 2px 10px rgba(30,50,90,.14)}
.app-bar{border-width:0;box-shadow:inset 2px 2px 2px -2px rgba(var(--gloss),calc(var(--gloss-hi) * 1 * var(--glass-specular))),inset 6px 6px 12px -8px rgba(var(--gloss),calc(var(--gloss-hi) * 0.5 * var(--glass-specular))),inset -2px -2px 2px -2px rgba(var(--gloss),calc(var(--gloss-hi) * 0.45 * var(--glass-specular))),inset -6px -6px 12px -8px rgba(var(--gloss),calc(var(--gloss-hi) * 0.2 * var(--glass-specular))),inset 0 0 22px rgba(var(--gloss),.07),inset 0 -2px 5px -2px var(--glass-inner),0 12px 40px var(--glass-drop),inset 0 0 0 .5px rgba(var(--gloss),calc(var(--gloss-border) * var(--glass-specular)))}
.group::after,.app-bar::after,#sheet::after{content:"";position:absolute;inset:0;border-radius:inherit;padding:1.5px;pointer-events:none;z-index:2;opacity:var(--glass-specular);
 background:conic-gradient(from 200deg at 50% 50%,rgba(var(--gloss),0.950) 0deg,rgba(var(--gloss),0.908) 8deg,rgba(var(--gloss),0.790) 16deg,rgba(var(--gloss),0.617) 24deg,rgba(var(--gloss),0.421) 32deg,rgba(var(--gloss),0.240) 40deg,rgba(var(--gloss),0.105) 48deg,rgba(var(--gloss),0.043) 56deg,rgba(var(--gloss),0.040) 64deg,rgba(var(--gloss),0.040) 72deg,rgba(var(--gloss),0.040) 80deg,rgba(var(--gloss),0.040) 88deg,rgba(var(--gloss),0.040) 96deg,rgba(var(--gloss),0.040) 104deg,rgba(var(--gloss),0.040) 112deg,rgba(var(--gloss),0.040) 120deg,rgba(var(--gloss),0.040) 128deg,rgba(var(--gloss),0.040) 136deg,rgba(var(--gloss),0.051) 144deg,rgba(var(--gloss),0.095) 152deg,rgba(var(--gloss),0.169) 160deg,rgba(var(--gloss),0.258) 168deg,rgba(var(--gloss),0.350) 176deg,rgba(var(--gloss),0.428) 184deg,rgba(var(--gloss),0.481) 192deg,rgba(var(--gloss),0.500) 200deg,rgba(var(--gloss),0.474) 208deg,rgba(var(--gloss),0.401) 216deg,rgba(var(--gloss),0.298) 224deg,rgba(var(--gloss),0.188) 232deg,rgba(var(--gloss),0.098) 240deg,rgba(var(--gloss),0.047) 248deg,rgba(var(--gloss),0.040) 256deg,rgba(var(--gloss),0.040) 264deg,rgba(var(--gloss),0.040) 272deg,rgba(var(--gloss),0.040) 280deg,rgba(var(--gloss),0.040) 288deg,rgba(var(--gloss),0.040) 296deg,rgba(var(--gloss),0.040) 304deg,rgba(var(--gloss),0.040) 312deg,rgba(var(--gloss),0.045) 320deg,rgba(var(--gloss),0.161) 328deg,rgba(var(--gloss),0.394) 336deg,rgba(var(--gloss),0.661) 344deg,rgba(var(--gloss),0.871) 352deg,rgba(var(--gloss),0.950) 360deg);
 -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude}
/* Keep the glass silhouette without continuously filtering the moving backdrop. */
[data-rendering="performance"] .blob{animation:none}
[data-rendering="performance"] #wallpaper{filter:none;transition:none}
[data-rendering="performance"] :is(.glass,#searchInput,#warnBar,#state-overlay){-webkit-backdrop-filter:blur(min(var(--glass-blur),8px));backdrop-filter:blur(min(var(--glass-blur),8px))}
[data-rendering="performance"] :is(.group,.chip,.icon-btn,.app-bar .bubble){-webkit-backdrop-filter:none;backdrop-filter:none}
[data-rendering="performance"] .group{background-color:rgba(var(--glass-tint-dark),max(var(--glass-opacity),.35))}
[data-rendering="performance"] :is(.glass,.group){box-shadow:inset 0 1px 0 rgba(var(--gloss),calc(.25 * var(--glass-specular))),0 4px 12px var(--glass-drop-sm);transition:background-color 160ms var(--ease-out)}
[data-rendering="performance"] :is(.group,.app-bar,#sheet)::after{display:none}
[data-rendering="performance"] .skel{animation:none}
#focusView{display:none;position:fixed;inset:0;z-index:25;padding:18px 16px 14px;gap:14px;flex-direction:column}
body.focusing #focusView{display:flex}
body.focusing #app,body.focusing #sheet,body.focusing #sheet-backdrop,body.focusing #wc{display:none}
body.focusing .blob{animation:none}
.focus-head{display:flex;align-items:center;gap:12px;flex-shrink:0;min-height:32px}
.focus-head h1{font-size:.875rem;font-weight:600;flex:1;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;color:var(--text-secondary)}
.focus-head .icon-btn{width:30px;height:30px;flex-shrink:0}
.focus-session{text-align:center;flex-shrink:0;padding:2px 0 6px}
#focusMode{font-size:.6875rem;letter-spacing:.12em;text-transform:uppercase;color:var(--text-secondary);margin-bottom:4px}
#focusTimer{font-size:2.5rem;font-weight:300;letter-spacing:.025em;font-variant-numeric:tabular-nums;line-height:1.15}
#focusDetails{flex:1;min-height:0;overflow:auto;padding:20px;border-radius:24px;overflow-wrap:anywhere;scrollbar-width:thin}
.focus-task-meta{display:flex;align-items:baseline;justify-content:space-between;gap:10px;font-size:.75rem;color:var(--text-secondary);margin-bottom:10px}
.focus-task-meta .badge{flex-shrink:0}
.focus-task-title{font-size:1.25rem;line-height:1.3;letter-spacing:-.02em;margin-bottom:20px}
.focus-instructions{font-size:.9375rem;line-height:1.6;white-space:pre-wrap}
#focusDetails h3,#focusDetails h4{font-size:.6875rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--text-secondary);margin-bottom:8px}
.focus-resources{margin-top:22px}
.focus-source{display:inline-flex;align-items:center;gap:6px;color:var(--blue);font-size:.8125rem;padding:8px 0;margin-top:12px}
.focus-source svg{width:14px;height:14px}
.focus-actions{flex-shrink:0;width:100%;align-self:center;user-select:none}
.focus-action:hover,.focus-action[aria-pressed="true"]{color:var(--text)}
.focus-action>.bubble{display:block;inset:0;width:auto;opacity:0;transition:opacity 120ms var(--ease-out);pointer-events:none}
.focus-action[aria-pressed="true"]>.bubble{opacity:1}
.focus-action>svg,.focus-action>span:not(.bubble){position:relative;z-index:1}
body.focusing .focus-action{transition:transform 140ms var(--ease-out),color 140ms var(--ease-out)}
body.focusing .focus-action:not(:disabled):focus-visible>.bubble{opacity:1}
@media (hover:hover) and (pointer:fine){
body.focusing .focus-action:not(:disabled):hover{transform:translateY(-1px) scale(1.03)}
body.focusing .focus-action:not(:disabled):hover>.bubble{opacity:1}
}
body.focusing .focus-action:not(:disabled):active{transform:scale(.96);transition-duration:60ms}
body.focusing .focus-action:not(:disabled):active>.bubble{opacity:1;transition-duration:0s}
body.focusing.reduce-motion .focus-action{transform:none !important;transition:none}
body.focusing.reduce-motion .focus-action>.bubble{transition:none}
@media (prefers-reduced-motion:reduce){body.focusing .focus-action{transform:none !important;transition:none}body.focusing .focus-action>.bubble{transition:none}}
.focus-actions .focus-action:disabled{opacity:1;color:var(--green);cursor:default}
.focus-actions .focus-action:disabled:hover{background:none}
#focusStatus{font-size:.75rem;line-height:1.4;color:var(--text-secondary);flex-shrink:0;text-align:center}
#focusStatus:empty{display:none}
@media (max-height:460px){#focusView{gap:10px;padding:12px}.focus-session{padding:0}#focusTimer{font-size:2rem}#focusDetails{padding:16px}.focus-task-title{margin-bottom:14px}}
@media (prefers-reduced-motion:reduce){.task-focus,.focus-actions .focus-action{transition:none}.focus-actions .focus-action:active{transform:none}}
</style>
</head>
<body>

<div id="wallpaper"><div class="blob b1"></div><div class="blob b2"></div><div class="blob b3"></div><div class="blob b4"></div><div class="blob b5"></div></div>
<section id="focusView" aria-label="Task focus">
<div class="focus-head pywebview-drag-region"><h1 id="focusTitle">Focus</h1><button class="icon-btn" id="focusMinimize" aria-label="Minimize">&#8722;</button></div>
<div class="focus-session"><p id="focusMode">Focused time</p><div id="focusTimer" role="timer" aria-label="Focus time">00:00:00</div></div>
<div id="focusDetails" class="glass" tabindex="0" aria-label="Task instructions"></div>
<p id="focusStatus" role="status" aria-live="polite"></p>
<nav class="focus-actions app-bar glass" aria-label="Focus actions"><button class="focus-action" id="focusPause">Pause</button><button class="focus-action" id="focusTop" aria-label="Keep on top" aria-pressed="false">On top</button><button class="focus-action" id="focusComplete" aria-label="Mark complete">Done</button><button class="focus-action" id="focusEnd" aria-label="Exit focus">Exit</button></nav></section>

<div id="wc">
  <button class="wc-btn" id="wcMin" aria-label="Minimize"></button>
  <button class="wc-btn" id="wcMax" aria-label="Maximize"></button>
  <button class="wc-btn" id="wcClose" aria-label="Close"></button>
</div>
<div id="grips"><div class="grip" data-edge="n"></div><div class="grip" data-edge="s"></div><div class="grip" data-edge="e"></div><div class="grip" data-edge="w"></div><div class="grip" data-edge="ne"></div><div class="grip" data-edge="nw"></div><div class="grip" data-edge="se"></div><div class="grip" data-edge="sw"></div></div>

<div id="app">
  <div id="top">
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
    <input id="searchInput" type="text" autocomplete="off" spellcheck="false" placeholder="Search tasks, notes, lessons, grades and LVS...">
    <button id="searchClear" aria-label="Clear search"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg></button>
  </div>
  <div id="chips"></div>
  <div id="warnBar" role="status"></div>
  </div>
  <main id="scroll"></main>

  <nav id="tabbar" class="app-bar glass">
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
    <button class="tab" data-tab="lvs"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 4H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-4"/><rect x="9" y="2" width="6" height="4" rx="1"/><path d="M7 11h10M7 16h7"/></svg><span>LVS</span></button>
  </nav>
</div>

<div id="sheet-backdrop"></div>
<div id="sheet" class="glass" role="dialog" aria-modal="true" aria-labelledby="sheetTitle" tabindex="-1">
  <div class="sheet-grabber"></div>
  <div class="sheet-head">
    <h2 id="sheetTitle">Detail</h2>
    <button class="sheet-close" id="sheetClose" aria-label="Close"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
  </div>
  <div class="sheet-scroll" id="sheetBody"></div>
</div>

<div id="toast" role="status" aria-live="polite"><span id="toastMsg"></span><button id="toastUndo" tabindex="-1">Undo</button></div>
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
function syncNow(){ var api = bridge(); if (!api || (BOOT && BOOT.chooseRendering)) return; showLoading(); api.sync_now(); }
var stateWriteQueue=Promise.resolve();
function queueStateWrite(work){var result=stateWriteQueue.then(work);stateWriteQueue=result.catch(function(){});return result;}
async function persistState(method,args,storage,value){
  var api=bridge();
  if(EMBEDDED){if(!api || !await api[method].apply(api,args))throw new Error('save failed');}
  else localStorage.setItem(storage,JSON.stringify(value));
}
function markTask(id,done){return queueStateWrite(async function(){
  var next=COMPLETED.filter(function(value){return value!==id;});if(done)next.push(id);
  try{await persistState('mark_task',[id,!!done],'planner.completed',next);COMPLETED=next;render(DATA,COMPLETED,{keepScroll:true});return true;}
  catch(e){render(DATA,COMPLETED,{keepScroll:true});showToast('Completion could not be saved. Please try again.');return false;}
});}
function openExternal(url){ var api = bridge(); if (api) api.open_external(url); else window.open(url, "_blank"); }
function saveSetting(key,val){
  return queueStateWrite(async function(){
    var next=Object.assign({},SETTINGS);next[key]=val;
    try{await persistState('save_setting',[key,val],'planner.settings',next);SETTINGS=next;return true;}
    catch(e){showToast('This setting could not be saved. Please try again.');return false;}
  });
}
function loadSetting(key){ return (key in SETTINGS) ? SETTINGS[key] : null; }
function togglePin(id){return queueStateWrite(async function(){
  var on=PINNED.indexOf(id)===-1,next=PINNED.filter(function(value){return value!==id;});if(on)next.push(id);
  try{await persistState('pin_task',[id,on],'planner.pinned',next);PINNED=next;return on;}
  catch(e){showToast('Pin could not be saved. Please try again.');return null;}
});}
function saveNote(id,text){return queueStateWrite(async function(){
  text=(text||'').trim();var next=Object.assign({},NOTES);if(text)next[id]=text;else delete next[id];
  try{await persistState('save_note',[id,text],'planner.notes',next);NOTES=next;return true;}
  catch(e){showToast('Note was not saved. Your text is still here; copy it or try again.');return false;}
});}
if (!EMBEDDED) {
  try { var _p = JSON.parse(localStorage.getItem("planner.pinned") || "[]"); if (Array.isArray(_p)) PINNED = _p; } catch(e){}
  try { var _n = JSON.parse(localStorage.getItem("planner.notes") || "{}"); if (_n && typeof _n === "object") NOTES = _n; } catch(e){}
}
if (!EMBEDDED) { try { var _s = JSON.parse(localStorage.getItem("planner.settings") || "{}"); for (var _k in _s) if (!(_k in SETTINGS)) SETTINGS[_k] = _s[_k]; } catch(e){} }
document.documentElement.setAttribute('data-rendering', renderingMode());

/* ===== STATE ===== */
var activeTab = "todo", activeCourse = "All", completedOpen = false, sheetLink = null;
var activeType = '';
var typeMenu = null, typeSearch = '', typeSearchAt = 0;
var TABS = ["todo","missed","schedule","all","grades","lvs"];
var TAB_TITLES = { todo:"Planner", missed:"Missed", schedule:"Schedule", all:"All Classes", grades:"Grades", lvs:"LVS" };
var searchQuery = "", noteTimer = null;
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
var SHORT_DATE = new Intl.DateTimeFormat("en-GB", {weekday:"short",day:"numeric",month:"short"});
var LONG_DATE = new Intl.DateTimeFormat("en-GB", {weekday:"long",day:"numeric",month:"long"});
var SHORT_WEEKDAY = new Intl.DateTimeFormat("en-GB", {weekday:"short"});
var LONG_WEEKDAY = new Intl.DateTimeFormat("en-GB", {weekday:"long"});
function formattedDay(iso, formatter){ var day = parseDay(iso); return isNaN(day.getTime()) ? "Invalid Date" : formatter.format(day); }
function fmtDate(iso){ return iso ? formattedDay(iso, SHORT_DATE) : "-"; }
function fmtLong(iso){ return iso ? formattedDay(iso, LONG_DATE) : "-"; }
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
  focus:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3H5a2 2 0 0 0-2 2v3m13-5h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3m13-5v3a2 2 0 0 1-2 2h-3"/><circle cx="12" cy="12" r="3"/></svg>',
  pause:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M9 5v14M15 5v14"/></svg>',
  play:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="m8 4 12 8-12 8z"/></svg>',
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
  closeTypeMenu(false);
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
  else if (activeTab==="lvs") html = renderLvs(data);
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
  if (activeTab !== "todo" && activeTab !== "missed") { if (el.__chipsHTML !== "") el.innerHTML = ""; el.__chipsHTML = ""; return; }
  var seen = {}, courses = ["All"];
  data.todos.forEach(function(t){ if (!seen[t.course]) { seen[t.course]=1; courses.push(t.course); } });
  var types = new Set();
  (data.assignment_types||[]).forEach(function(t){if(t.visible && t.name) types.add(t.name);});
  data.todos.forEach(function(t){types.add(taskType(t));});
  types.delete('');
  if (activeType && !types.has(activeType)) activeType = '';
  var typeList=Array.from(types).sort(function(a,b){return a.localeCompare(b);});
  el.__taskTypes=typeList;
  var html = '<button class="chip type-filter" aria-label="Task type: '+esc(activeType||'All types')+'" aria-haspopup="listbox" aria-expanded="false" aria-controls="taskTypeMenu" id="taskTypeFilter"><span>'+esc(activeType||'All types')+'</span><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></button>';
  if (activeTab === 'todo') html += courses.map(function(c){ return '<button class="chip'+(c===activeCourse?" active":"")+'" aria-pressed="'+(c===activeCourse?"true":"false")+'" data-course="'+esc(c)+'">'+esc(c)+'</button>'; }).join("");
  if (el.__chipsHTML !== html) { el.innerHTML = html; el.__chipsHTML = html; }
}

function taskType(task){
  var raw = String(task.type||'').trim(), key = raw.toLocaleLowerCase();
  if (!key) return '';
  var type = (DATA.assignment_types||[]).find(function(t){return String(t.name||'').trim().toLocaleLowerCase()===key || String(t.abbreviation||'').trim().toLocaleLowerCase()===key;});
  return type ? type.name : raw;
}
function matchesType(task){return !activeType || taskType(task)===activeType;}

function closeTypeMenu(restore){
  if(!typeMenu || !typeMenu.classList.contains('open'))return;
  typeMenu.classList.remove('open');typeMenu.setAttribute('inert','');typeMenu.setAttribute('aria-hidden','true');
  var trigger=document.getElementById('taskTypeFilter');
  if(trigger){trigger.setAttribute('aria-expanded','false');if(restore)trigger.focus({preventScroll:true});}
}
function openTypeMenu(keyboard,last){
  var trigger=document.getElementById('taskTypeFilter');if(!trigger)return;
  if(!typeMenu){
    typeMenu=document.createElement('div');typeMenu.id='taskTypeMenu';typeMenu.className='type-menu glass';
    typeMenu.setAttribute('role','listbox');typeMenu.setAttribute('aria-label','Task type');document.body.appendChild(typeMenu);
    typeMenu.addEventListener('click',function(e){
      var option=e.target.closest('[data-task-type]');if(!option)return;
      activeType=option.dataset.taskType;closeTypeMenu(false);render(DATA,COMPLETED);
      document.getElementById('taskTypeFilter').focus({preventScroll:true});
    });
    typeMenu.addEventListener('keydown',function(e){
      var options=Array.from(typeMenu.querySelectorAll('[role="option"]')), index=options.indexOf(document.activeElement), next=index;
      if(e.key==='Tab'){closeTypeMenu(true);return;}
      if(e.key==='ArrowDown')next=(index+1)%options.length;
      else if(e.key==='ArrowUp')next=(index-1+options.length)%options.length;
      else if(e.key==='Home')next=0;
      else if(e.key==='End')next=options.length-1;
      else if(e.key==='Enter' || e.key===' '){e.preventDefault();if(index>=0)options[index].click();return;}
      else if(e.key.length===1 && !e.ctrlKey && !e.metaKey && !e.altKey){
        var now=performance.now();typeSearch=(now-typeSearchAt>700?'':typeSearch)+e.key.toLocaleLowerCase();typeSearchAt=now;
        next=options.findIndex(function(option){return option.textContent.trim().toLocaleLowerCase().startsWith(typeSearch);});
        if(next<0)next=index;
      }else return;
      e.preventDefault();if(next>=0){options[next].focus({preventScroll:true});options[next].scrollIntoView({block:'nearest'});}
    });
  }
  typeSearch='';typeSearchAt=0;
  typeMenu.innerHTML=[''].concat(document.getElementById('chips').__taskTypes||[]).map(function(type,i){
    return '<button class="type-menu-option" role="option" tabindex="-1" aria-selected="'+(type===activeType)+'" data-task-type="'+esc(type)+'" style="--item-delay:'+Math.min(i*12,60)+'ms"><span>'+esc(type||'All types')+'</span>'+(type===activeType?'<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m4 10 4 4 8-8"/></svg>':'')+'</button>';
  }).join('');
  typeMenu.classList.toggle('instant',!!keyboard || document.body.classList.contains('reduce-motion'));
  var rect=trigger.getBoundingClientRect(), width=Math.min(Math.max(rect.width,260),window.innerWidth-24);
  var below=window.innerHeight-rect.bottom-20, above=rect.top-20, up=below<180 && above>below;
  typeMenu.style.width=width+'px';typeMenu.style.maxHeight=Math.max(60,Math.min(360,up?above:below))+'px';
  typeMenu.style.left=Math.max(12,Math.min(rect.left,window.innerWidth-width-12))+'px';
  typeMenu.style.top=up?'auto':(rect.bottom+8)+'px';typeMenu.style.bottom=up?(window.innerHeight-rect.top+8)+'px':'auto';
  typeMenu.style.transformOrigin=up?'bottom left':'top left';
  typeMenu.scrollTop=0;lensScan();void typeMenu.offsetWidth;
  typeMenu.removeAttribute('inert');typeMenu.removeAttribute('aria-hidden');typeMenu.classList.add('open');trigger.setAttribute('aria-expanded','true');
  var options=typeMenu.querySelectorAll('[role="option"]'), selected=typeMenu.querySelector('[aria-selected="true"]');
  (last?options[options.length-1]:selected||options[0]).focus({preventScroll:true});
  if(selected && !last)selected.scrollIntoView({block:'nearest'});
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

function canFocus(type){return !/\b(meenemen|meebrengen|meebreng|herinnering|herinneringen|reminder|reminders|materiaal|materialen)\b|^ME$/i.test(String(type||'').normalize('NFKC').trim());}
function taskRow(t, completed){
  var done = completed.indexOf(t.id)!==-1, pinned = PINNED.indexOf(t.id)!==-1;
  var extras = (t.attachments && t.attachments.length ? '<span style="color:var(--text-tertiary)">&middot;</span><span>'+ICON.clip+t.attachments.length+'</span>' : "")+
    (t.weblinks && t.weblinks.length ? '<span style="color:var(--text-tertiary)">&middot;</span><span>'+ICON.clip.replace("mini","mini")+t.weblinks.length+' link'+(t.weblinks.length>1?"s":"")+'</span>' : "");
  var cls = "task-row"+(done?" done":"")+(isOverdue(t)?" overdue":"")+(t.warning?" warning":"");
  return '<div class="'+cls+'" role="listitem" data-detail="task" data-id="'+esc(t.id)+'">'+
    '<div class="check'+(done?" done":"")+(t.warning?" warn-ring":"")+'" data-check="'+esc(t.id)+'" role="checkbox" tabindex="0" aria-checked="'+(done?"true":"false")+'" aria-label="Mark done: '+esc(t.description)+'"></div>'+
    '<div class="task-body" tabindex="0" role="button"><div class="task-line1"><span class="task-course">'+esc(t.course)+'</span>'+badges(t)+'</div>'+
    '<div class="task-desc">'+esc(t.description)+'</div>'+
    (infoText(t) ? '<div class="task-info">'+esc(infoText(t))+'</div>' : "")+
    (NOTES[t.id] ? '<div class="task-note">'+ICON.note+esc(NOTES[t.id])+'</div>' : "")+
    '<div class="task-meta"><span>'+relLabel(t.due_date)+'</span><span style="color:var(--text-tertiary)">&middot;</span><span>posted '+fmtDate(t.posted_date)+'</span>'+extras+'</div></div>'+
    '<div class="task-row-actions">'+(canFocus(t.type)?'<button class="task-focus" data-focus-id="'+esc(t.id)+'" aria-label="Focus on '+esc(t.description)+'" title="Focus">'+ICON.focus+'</button>':'')+
    '<button class="task-pin'+(pinned?" on":"")+'" data-pin="'+esc(t.id)+'" aria-label="'+(pinned?"Unpin":"Pin")+'" title="'+(pinned?"Unpin":"Pin to top")+'">'+ICON.pin+'</button></div></div>';
}

function infoText(t){ return t && t.body && t.body.trim() && t.body.trim()!==(t.description||"").trim() ? t.body.trim() : ""; }
function empty(title, msg, icon, compact){ var act = (EMBEDDED && /^No (grades|schedule|classes)/.test(title) && !compact) ? '<button class="retry-btn secondary" data-sync-now>Sync now</button>' : ""; return '<div class="empty'+(compact?" compact":"")+'">'+icon+'<h3>'+title+'</h3><p>'+msg+'</p>'+act+'</div>'; }

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
  if (w.peak >= 0) out += " Busiest day: " + LONG_WEEKDAY.format(parseDay(w.days[w.peak].date)) + " (" + w.days[w.peak].n + (w.days[w.peak].n === 1 ? " item" : " items") + ").";
  return out;
}
function renderOverview(data, completed){
  var w = weekStats(data, completed), max = 1;
  w.days.forEach(function(d){ if (d.score > max) max = d.score; });
  var bars = w.days.map(function(d, i){
    var cls = "busy-col" + (d.score === 0 ? " zero" : d.score >= 6 ? " high" : d.score >= 3 ? " mid" : "") + (i === 0 ? " today" : "");
    var label = SHORT_WEEKDAY.format(parseDay(d.date));
    var tip = fmtDate(d.date) + ": " + d.n + (d.n === 1 ? " task" : " tasks") + (d.tests ? ", " + d.tests + (d.tests === 1 ? " test" : " tests") : "");
    return '<div class="'+cls+'" tabindex="0" role="img" data-tip="'+esc(tip)+'" aria-label="'+esc(tip)+'"><span class="busy-n">'+(d.n||"")+'</span><div class="busy-bar" style="height:'+Math.max(4, Math.round(d.score / max * 58))+'px"></div><span class="busy-day">'+(i===0?"Today":label)+'</span></div>';
  }).join("");
  return '<div class="section"><div class="section-header" role="heading" aria-level="2">Week ahead</div><div class="group overview">'+
    '<div class="summary-text">'+esc(localSummary(w))+'</div>'+
    '<div class="busy">'+bars+'</div><div class="busy-legend">Busier days are taller &middot; tests count extra</div></div></div>';
}

function renderTodo(data, completed){
  var searching = searchActive();
  function pass(t){ return (activeCourse==="All" || t.course===activeCourse) && matchesType(t) && matchTask(t); }
  var open = data.todos.filter(function(t){ return completed.indexOf(t.id)===-1 && pass(t); });
  var pinned = open.filter(function(t){ return PINNED.indexOf(t.id)!==-1; });
  var todos = open.filter(function(t){ return PINNED.indexOf(t.id)===-1 && !isOverdue(t); });
  var g = { "Today":[], "Tomorrow":[], "This week":[], "Later":[] };
  todos.forEach(function(t){
    var d = daysBetween(TODAY, t.due_date);
    (d===0 ? g["Today"] : d===1 ? g["Tomorrow"] : d<7 ? g["This week"] : g["Later"]).push(t);
  });
  var html = (!searching && activeCourse==="All" && !activeType) ? renderOverview(data, completed) : "";
  if (pinned.length) html += '<div class="section"><div class="section-header" role="heading" aria-level="2">Pinned<span class="count">'+pinned.length+'</span></div><div class="group" role="list">'+pinned.map(function(t){ return taskRow(t, completed); }).join("")+'</div></div>';
  var shown = pinned.length;
  Object.keys(g).forEach(function(k){
    if (!g[k].length) return;
    shown += g[k].length;
    html += '<div class="section"><div class="section-header" role="heading" aria-level="2">'+k+'<span class="count">'+g[k].length+'</span></div><div class="group" role="list">'+g[k].map(function(t){ return taskRow(t, completed); }).join("")+'</div></div>';
  });
  var done = data.todos.filter(function(t){ return completed.indexOf(t.id)!==-1 && pass(t); })
    .sort(function(a,b){ return a.due_date < b.due_date ? 1 : -1; });
  if (!shown) html += activeType && !done.length ? empty('No matching tasks','No tasks match the selected filters.',ICON.search) : searching && !done.length ? noMatches()
    : empty("All caught up", done.length ? done.length+" completed. Nothing else due right now." : "Nothing due right now. Enjoy the calm.", ICON.ok, done.length>0);
  if (done.length) html += completedSection(done, completed);
  return html;
}

function completedSection(done, completed){
  return '<div class="section"><button class="completed-toggle'+(completedOpen?" open":"")+'" data-toggle-completed="1"><span>Completed</span><span class="meta">'+done.length+
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 6 15 12 9 18"/></svg></span></button>'+
    (completedOpen ? '<div class="group" role="list">'+done.map(function(t){ return taskRow(t, completed); }).join("")+'</div>' : "")+'</div>';
}

function renderMissed(data, completed){
  var list = data.todos.filter(function(t){ return isMissed(t, completed) && matchesType(t) && matchTask(t); });
  if (!list.length) return activeType ? empty('No matching tasks','No missed tasks match the selected filters.',ICON.search) : searchActive() ? noMatches() : empty("All caught up","No missed tasks from the last 7 days.",ICON.clock);
  return '<div class="section"><div class="section-header" role="heading" aria-level="2">Last 7 days<span class="count">'+list.length+'</span></div><div class="group" role="list">'+list.map(function(t){ return taskRow(t, completed); }).join("")+'</div></div>';
}

function lessonRow(ev, completed, withAssign){
  var assign = "";
  if (withAssign && ev.info) ev.info.assignments.forEach(function(a){
    var done = completed.indexOf(a.id)!==-1;
    assign += '<div class="lesson-assign" data-detail="task" data-id="'+esc(a.id)+'"><div class="check'+(done?" done":"")+'" data-check="'+esc(a.id)+'" role="checkbox" tabindex="0" aria-checked="'+(done?"true":"false")+'" aria-label="Mark done: '+esc(a.description)+'"></div>'+
      '<div><div style="font-weight:500">'+esc(a.description)+'</div><div style="font-size:12px;color:var(--text-secondary);margin-top:4px;display:flex;gap:6px;flex-wrap:wrap;align-items:center">'+badges(a)+' due '+relLabel(a.due_date)+'</div></div></div>';
  });
  var sub = [ev.classroom, ev.teacher, ev.groups].filter(Boolean).map(esc).join(" &middot; ");
  return '<div class="lesson-row" role="listitem" data-detail="lesson" data-moment="'+esc(ev.moment_id)+'">'+
    '<div class="lesson-time">'+esc(ev.start)+'<span class="end">'+esc(ev.end)+'</span></div>'+
    '<div class="lesson-bar" style="background:var('+courseVar(ev.course)+')"></div>'+
    '<div class="lesson-body" tabindex="0" role="button"><div class="lesson-title">'+esc(ev.course)+(ev.title?' <span style="color:var(--text-secondary);font-weight:400">&middot; '+esc(ev.title)+'</span>':"")+'</div>'+
    '<div class="lesson-sub">'+sub+'</div>'+
    (ev.note?'<div class="lesson-sub" style="color:var(--orange)">Note: '+esc(ev.note)+'</div>':"")+assign+'</div></div>';
}

function dayBlocks(days, completed, withAssign, emptyMsg){
  return days.map(function(day){
    var body = day.events.length ? day.events.map(function(ev){ return lessonRow(ev, completed, withAssign); }).join("") : '<div class="lesson-row" style="cursor:default"><div class="lesson-sub">'+emptyMsg+'</div></div>';
    var tag = day.date===TODAY ? ' <span class="today-tag">Today</span>' : "";
    return '<div class="section" data-date="'+esc(day.date)+'"><div class="section-header" role="heading" aria-level="2">'+fmtLong(day.date)+tag+'</div><div class="group" role="list">'+body+'</div></div>';
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
    html += '<div class="section"><div class="section-header" role="heading" aria-level="2"><span>'+esc(c)+avgPill(averageOf(by[c]))+'</span><span class="count">'+by[c].length+'</span></div><div class="group">'+
      by[c].map(function(r){
        return '<div class="grade-row" data-detail="grade" data-id="'+esc(r.id)+'" tabindex="0" role="button"><div><div class="grade-name">'+esc(r.name || "Evaluation")+'</div><div class="grade-meta">'+esc(fmtDate(r.date))+(r.counts ? "" : " &middot; doesn&rsquo;t count")+'</div></div>'+
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

function lvsReadKey(){return 'lvsRead:'+JSON.stringify([DATA.main_url||'',DATA.user_id||'',(DATA.lvs||{}).since||'']);}
function lvsItemKey(kind,id){return kind+':'+String(id);}
function lvsUnread(kind,id){var read=SETTINGS[lvsReadKey()];return !Array.isArray(read) || read.indexOf(lvsItemKey(kind,id))===-1;}
function unreadDot(){return '<span class="unread-dot" role="img" aria-label="Unread"></span>';}
var lvsReadQueue=Promise.resolve();
function saveLvsRead(items){
  var key=lvsReadKey();
  // Serialize single-item and bulk saves so a slower request cannot undo a newer read.
  lvsReadQueue=lvsReadQueue.then(async function(){
    var previous=SETTINGS[key], next=Array.from(new Set((Array.isArray(previous)?previous:[]).concat(items)));
    try {
      var api=bridge();
      if (EMBEDDED) {if (!api || !await api.save_setting(key,next)) throw new Error('save');}
      else localStorage.setItem('planner.settings',JSON.stringify(Object.assign({},SETTINGS,{[key]:next})));
      SETTINGS[key]=next;
    } catch(e) {
      showToast('Could not save read status. Please try again.');
    }
    document.querySelectorAll('#scroll .lvs-item').forEach(function(row){
      var kind=row.hasAttribute('data-lvs-note')?'notes':'absences', itemId=row.dataset.lvsNote||row.dataset.lvsAbsence;
      var dot=row.querySelector('.unread-dot');
      if(dot && !lvsUnread(kind,itemId))dot.remove();
    });
    updateTabs();
    var button=document.querySelector('[data-lvs-read-all]');
    if(button)button.disabled=!hasUnreadLvs();
  });
  return lvsReadQueue;
}
function markLvsRead(kind,id){
  if (!lvsUnread(kind,id)) return Promise.resolve();
  return saveLvsRead([lvsItemKey(kind,id)]);
}
function hasUnreadLvs(){return ['notes','absences'].some(function(kind){return ((DATA.lvs||{})[kind]||[]).some(function(item){return lvsUnread(kind,item.id);});});}
async function markAllLvsRead(button){
  button.disabled=true;button.setAttribute('aria-busy','true');
  var items=[];
  ['notes','absences'].forEach(function(kind){((DATA.lvs||{})[kind]||[]).forEach(function(item){items.push(lvsItemKey(kind,item.id));});});
  try {await saveLvsRead(items);} finally {button.removeAttribute('aria-busy');button.disabled=!hasUnreadLvs();}
}
function openLvsAbsence(id){
  var item=((DATA.lvs||{}).absences||[]).find(function(a){return String(a.id)===id;});if(!item)return;
  showSheet(item.description||'Absence','<div class="detail-block"><div class="detail-list">'+rows([['Date',fmtLong((item.date||'').slice(0,10))],['Part of day',item.part],['Code',item.code],['Description',item.description],['Information',item.info]])+'</div></div>');
  markLvsRead('absences',id);
}
function renderLvs(data){
  var lvs = data.lvs;
  if (!lvs) return empty('LVS not synced', 'Sync to load your LVS notes and absences.', ICON.note)+'<button class="btn-secondary" data-sync-now>Sync now</button>';
  var html = '<div class="lvs-toolbar"><p class="header-subtitle">This school year'+(lvs.since?' · From '+esc(fmtLong(lvs.since)):'')+'</p><button class="chip" data-lvs-read-all'+(hasUnreadLvs()?'':' disabled')+'>Mark all as read</button></div>';
  ['notes','absences'].forEach(function(kind){
    var all = lvs[kind]||[], list = all.filter(function(item){return matchesText([item.title,item.category,item.author,item.date,item.code,item.description,item.info,item.part].join(' '));});
    html += '<section class="section"><div class="section-header">'+(kind==='notes'?'Notes':'Absences')+'<span class="count">'+list.length+'</span></div>';
    if (lvs[kind+'_error']) html += '<p class="detail-info" role="status">'+esc(lvs[kind+'_error'])+'</p>';
    if (!list.length) {
      if (!lvs[kind+'_error']) html += searchActive() && all.length ? noMatches() : empty(kind==='notes'?'No LVS notes':'No absences','Nothing available for this school year.',ICON.note,true);
    } else html += '<div class="group">'+list.map(function(item){
      var date = (item.date||'').slice(0,10);
      var dot=lvsUnread(kind,item.id)?unreadDot():'';
      if (kind==='notes') return '<button class="grade-row lvs-item" data-lvs-note="'+esc(item.id)+'">'+dot+'<div><div class="grade-name">'+esc(item.title||item.category||'LVS note')+'</div><div class="grade-meta">'+esc([fmtDate(date),item.category,item.author].filter(Boolean).join(' · '))+'</div></div></button>';
      return '<button class="grade-row lvs-item" data-lvs-absence="'+esc(item.id)+'">'+dot+'<div><div class="grade-name">'+esc(item.description||item.code||'Absence')+'</div><div class="grade-meta">'+esc([fmtDate(date),item.part,item.code].filter(Boolean).join(' · '))+'</div>'+(item.info?'<div class="task-info">'+esc(item.info)+'</div>':'')+'</div></button>';
    }).join('')+'</div>';
    html += '</section>';
  });
  return html;
}
async function openLvsNote(id){
  var note = ((DATA.lvs||{}).notes||[]).find(function(item){return item.id===id;}); if (!note) return;
  var url = DATA.main_url?'https://'+DATA.main_url+'/?module=LVS':null;
  showSheet(note.title||'LVS note', '<div class="detail-block"><div class="detail-list">'+rows([['Category',note.category],['Date',fmtLong((note.date||'').slice(0,10))],['Author',note.author]])+'</div></div><div id="lvsNoteContent" role="status"><p class="detail-desc">Loading note...</p></div>'+linkButton(url), url);
  var target = document.getElementById('lvsNoteContent');
  try {
    var api = bridge();
    if (!api) throw new Error('Open this note in the desktop app or in Smartschool to read its contents.');
    var detail = await api.lvs_note_detail(id);
    if (!target.isConnected || !sheetEl.classList.contains('show')) return;
    if (!detail || detail.error) throw new Error(detail && detail.error || 'Could not load this note.');
    target.innerHTML = (detail.text?'<div class="detail-block"><h4>Note</h4><div class="detail-info">'+esc(detail.text)+'</div></div>':'')+
      '<div class="detail-block"><div class="detail-list">'+rows([['Category choice',detail.choice],['Date',detail.date?fmtLong(detail.date.slice(0,10)):'']].filter(function(p){return p[1];}).concat(Object.entries(detail.fields||{})))+'</div></div>'+
      ((detail.attachments||[]).length?'<div class="detail-block"><h4>Attachments</h4><div class="detail-info">'+detail.attachments.map(function(a){return esc(a.name||'Attachment');}).join('<br>')+'<p>Open Smartschool to download these files.</p></div></div>':'')+
      (!detail.text && !detail.choice && !Object.keys(detail.fields||{}).length && !(detail.attachments||[]).length?'<p class="detail-desc">No additional content.</p>':'');
    await markLvsRead('notes',id);
  } catch(e) {
    if (target.isConnected && sheetEl.classList.contains('show')) target.innerHTML = '<p class="detail-desc">'+esc(e.message||'Could not load this note.')+'</p><button class="btn-secondary" data-lvs-note="'+esc(id)+'">Try again</button>';
  }
}

function updateTabs(){
  document.querySelectorAll(".tab").forEach(function(t){ var on = t.dataset.tab===activeTab; t.classList.toggle("active", on); if (on) t.setAttribute("aria-current","page"); else t.removeAttribute("aria-current"); });
  var mb = document.getElementById("missedBadge"), mt = document.querySelector('.tab[data-tab="missed"]');
  mt.setAttribute("aria-label", mb.style.display === "none" ? "Missed" : "Missed, " + mb.textContent);
  var lt=document.querySelector('.tab[data-tab="lvs"]'), dot=lt.querySelector('.unread-dot');
  var unread=hasUnreadLvs();
  if(unread && !dot)lt.insertAdjacentHTML('beforeend',unreadDot());else if(!unread && dot)dot.remove();
  lt.setAttribute('aria-label',unread?'LVS, unread items':'LVS');
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
async function flushNote(){
  if (noteTimer) { clearTimeout(noteTimer); noteTimer = null; }
  var area = document.getElementById("noteArea");
  if (area && area.getAttribute("data-note") && (NOTES[area.getAttribute("data-note")] || "") !== area.value.trim()) {
    var text=area.value;
    if(!await saveNote(area.getAttribute("data-note"),text))return false;
    if(area.isConnected && area.value!==text)return flushNote();
    render(DATA, COMPLETED, { keepScroll: true });
  }
  return true;
}

function openTask(id, focus){
  var t = DATA.todos.filter(function(x){ return x.id===id; })[0], lesson = null, day = null;
  if (!t) DATA.days.concat(DATA.all_classes||[]).forEach(function(d){ d.events.forEach(function(ev){ if (ev.info) ev.info.assignments.forEach(function(a){ if (a.id===id && !t) { t=a; lesson=ev; day=d; } }); }); });
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
    extraBlock(t.detail_fields);
  var title = (t.course||(lesson&&lesson.course)||"Task")+" - "+(t.type||"Task");
  var focusBody = '<div class="focus-task-meta"><span class="badge">'+esc(t.type||'Task')+'</span><span>'+(t.due_date?'Due '+esc(relLabel(t.due_date)):'')+'</span></div><h2 class="focus-task-title">'+esc(t.description)+'</h2>'+
    (infoText(t)?'<h3>Instructions</h3><div class="focus-instructions">'+esc(infoText(t))+'</div>':'')+
    ((t.attachments||[]).length||(t.weblinks||[]).length?'<div class="focus-resources">'+linksBlock(t)+'</div>':'')+
    (link?'<button class="focus-source" data-external="1">'+ICON.ext+' Open in Smartschool</button>':'');
  focusCandidate = {id:t.id,title:title,body:focusBody,link:link};
  if (focus) {if (canFocus(t.type)) focusAction('start'); return;}
  showSheet(title, body+'<div class="task-actions">'+pinButton(t.id)+(canFocus(t.type)?'<button class="btn-secondary" data-focus-task="1">'+ICON.focus+' Focus</button>':'')+'</div>'+linkButton(link), link);
}

/* Desktop session state survives the page reload performed by sync. */
var focusCandidate = null, focusSession = null, focusTick = null, focusStamp = 0, focusBusy = false;
function focusClock(){
  if (!focusSession) return;
  var seconds = Math.floor(focusSession.elapsed+(focusSession.running?(performance.now()-focusStamp)/1000:0));
  document.getElementById('focusTimer').textContent = [Math.floor(seconds/3600),Math.floor(seconds/60)%60,seconds%60].map(function(n){return String(n).padStart(2,'0');}).join(':');
}
function showFocus(state){
  if (!state) return;
  var entering = !focusSession;
  focusSession = state; focusStamp = performance.now();
  if (entering) {
    hideSheet(); document.body.classList.add('focusing'); document.getElementById('app').setAttribute('inert','');
    document.getElementById('focusTitle').textContent = state.task.title;
    document.getElementById('focusDetails').innerHTML = state.task.body;
    document.getElementById('focusStatus').textContent = '';
    document.getElementById('focusPause').focus();
  }
  document.getElementById('focusPause').innerHTML = '<span class="bubble" aria-hidden="true"></span>'+(state.running?ICON.pause:ICON.play)+'<span>'+(state.running?'Pause':'Resume')+'</span>';
  document.getElementById('focusPause').setAttribute('aria-pressed',!state.running);
  document.getElementById('focusMode').textContent = state.running?'Focused time':'Paused';
  document.getElementById('focusTop').setAttribute('aria-pressed',!!state.onTop);
  document.getElementById('focusComplete').disabled = COMPLETED.indexOf(state.task.id)!==-1;
  lensScan();
  clearInterval(focusTick); focusClock(); if (state.running) focusTick = setInterval(focusClock,1000);
}
async function focusAction(action){
  if (focusBusy) return;
  focusBusy = true;
  try {
    var api = bridge();
    if (action === 'start') {
      if(!await flushNote())return; showFocus(api?await api.focus_start(focusCandidate):{task:focusCandidate,elapsed:0,running:true,onTop:false});
    } else if (action === 'pause') {
      if (api) showFocus(await api.focus_pause());
      else {var state = Object.assign({},focusSession); state.elapsed += state.running?(performance.now()-focusStamp)/1000:0; state.running = !state.running; showFocus(state);}
    } else if (action === 'top') {
      if (!api) throw new Error('Keep on top is available in the desktop app.');
      if (!await api.focus_on_top(!focusSession.onTop)) throw new Error('Could not change window position.');
      focusSession.onTop = !focusSession.onTop; document.getElementById('focusTop').setAttribute('aria-pressed',focusSession.onTop);
      lensScan();
    } else if (action === 'complete') {
      var id = focusSession.task.id;
      if (!await markTask(id,true)) throw new Error('Could not save completion.');
      document.getElementById('focusComplete').disabled = true;
      document.getElementById('focusStatus').textContent = 'Task marked complete. You can continue focusing or exit.';
    } else if (action === 'end') {
      if (api && !await api.focus_end()) throw new Error('Could not restore the window. Please try again.');
      clearInterval(focusTick); focusSession = null; document.body.classList.remove('focusing');
      document.getElementById('app').removeAttribute('inert'); render(DATA,COMPLETED,{keepScroll:true}); document.getElementById('settingsBtn').focus();
    }
  } catch(e) {
    if (focusSession) document.getElementById('focusStatus').textContent = e.message||'Focus action failed. Please try again.';
    else showToast('Could not start Focus. Please try again.');
  } finally {focusBusy = false;}
}
document.getElementById('focusPause').onclick = function(){focusAction('pause');};
document.getElementById('focusTop').onclick = function(){focusAction('top');};
document.getElementById('focusComplete').onclick = function(){focusAction('complete');};
document.getElementById('focusTop').innerHTML = '<span class="bubble" aria-hidden="true"></span>'+ICON.pin+'<span>On top</span>';
document.getElementById('focusComplete').innerHTML = '<span class="bubble" aria-hidden="true"></span>'+ICON.ok+'<span>Done</span>';
document.getElementById('focusEnd').innerHTML = '<span class="bubble" aria-hidden="true"></span>'+ICON.ext+'<span>Exit</span>';
document.getElementById('focusEnd').onclick = function(){focusAction('end');};
document.getElementById('focusMinimize').onclick = function(){winCall('win_minimize');};
document.getElementById('focusDetails').onclick = function(e){
  var link = e.target.closest('[data-open-url]');
  if (link) openExternal(link.getAttribute('data-open-url'));
  else if (e.target.closest('[data-external]')) {sheetLink = focusSession.task.link; openSmartschool();}
};
async function restoreFocusSession(){
  try {var api = bridge(); if (api) showFocus(await api.focus_state());} catch(e) {showToast('Could not restore Focus. Reload or restart the app.');}
}
window.addEventListener('pywebviewready',restoreFocusSession);

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

var sheetEl = document.getElementById("sheet"), scrimEl = document.getElementById("sheet-backdrop");
var INERT_IDS = ["header","chips","searchbar","warnBar","scroll","tabbar"], sheetRet = null, sheetAnim = 0, sheetY = 0, sheetH = 1;
var sheetNotice = null, noticeClosing = false;
function setInert(on){ INERT_IDS.forEach(function(id){ var el = document.getElementById(id); if (!el) return; if (on) el.setAttribute("inert",""); else el.removeAttribute("inert"); }); }
function sheetResetStyles(){
  cancelAnimationFrame(sheetAnim);
  if (!sheetEl.style.transform && !sheetEl.style.transition && !scrimEl.style.opacity) return;
  sheetEl.style.transition = "none"; scrimEl.style.transition = "none";
  sheetEl.style.transform = ""; scrimEl.style.opacity = "";
  void sheetEl.offsetHeight;
  sheetEl.style.transition = ""; scrimEl.style.transition = "";
}
function restoreFocus(){ if (sheetRet && document.body.contains(sheetRet) && sheetRet.focus) sheetRet.focus({preventScroll:true}); sheetRet = null; }
function showSheet(title, body, link, reuse){
  closeTypeMenu(false);
  sheetLink = link || null;
  if (!sheetEl.classList.contains("show")) sheetRet = document.activeElement;
  sheetResetStyles();
  var heading = document.getElementById("sheetTitle"), content = document.getElementById("sheetBody");
  if (heading.textContent !== title) heading.textContent = title;
  var rebuilt = !reuse || sheetEl.__body !== body;
  if (rebuilt) content.innerHTML = body;
  sheetEl.__body = reuse ? body : null;
  content.scrollTop = 0;
  // Install the final-size filter before the entrance, not during its first frames.
  if (rebuilt && LENS.ok) lensApplyBatch([sheetEl]);
  sheetEl.classList.add("show"); document.body.classList.add("sheet-open"); scrimEl.classList.add("show");
  setInert(true); sheetEl.focus({preventScroll:true});
  return rebuilt;
}
async function hideSheet(){
  if (!closeSheetNotice()) return;
  if(!await flushNote())return;
  if (!sheetEl.classList.contains("show")) return;
  cancelAnimationFrame(sheetAnim);
  // transitions resume from wherever the sheet is right now (no jump)
  sheetEl.style.transition = ""; scrimEl.style.transition = "";
  sheetEl.style.transform = ""; scrimEl.style.opacity = "";
  document.body.classList.remove("sheet-open"); sheetEl.classList.remove("show"); scrimEl.classList.remove("show");
  setInert(false); restoreFocus();
}
async function finishClose(){
  if (!closeSheetNotice()) return;
  if(!await flushNote()){sheetResetStyles();return;} cancelAnimationFrame(sheetAnim);
  sheetEl.style.transition = "none"; scrimEl.style.transition = "none";
  document.body.classList.remove("sheet-open"); sheetEl.classList.remove("show"); scrimEl.classList.remove("show");
  sheetEl.style.transform = ""; scrimEl.style.opacity = "";
  void sheetEl.offsetHeight;
  sheetEl.style.transition = ""; scrimEl.style.transition = "";
  setInert(false); restoreFocus();
}
/* drag to dismiss: finger-tracked, rubber-banded upward, momentum-projected release, critically damped spring */
(function(){
  var cand = null, d = null, samples = [];
  function reduced(){ return matchMedia("(prefers-reduced-motion:reduce)").matches || document.body.classList.contains("reduce-motion"); }
  function curY(){ return new DOMMatrixReadOnly(getComputedStyle(sheetEl).transform).m42; }
  function rb(o, dim){ return (o * dim * .55) / (dim + .55 * Math.abs(o)); }
  function setY(y){ sheetY = y; sheetEl.style.transform = "translate(0," + y + "px)"; scrimEl.style.opacity = Math.max(0, Math.min(1, 1 - y / sheetH)); }
  function spring(to, v0, done){
    cancelAnimationFrame(sheetAnim);
    var A = sheetY - to, w = 16, B = v0 + w * A, t0 = 0;
    function step(now){
      if (!t0) t0 = now;
      var t = (now - t0) / 1000, x = to + (A + B * t) * Math.exp(-w * t);
      setY(x);
      if (t < .7 && (Math.abs(x - to) > .5 || t < .04)) sheetAnim = requestAnimationFrame(step);
      else { setY(to); if (done) done(); }
    }
    sheetAnim = requestAnimationFrame(step);
  }
  function end(){
    if (!d) return;
    var id = d.id; d = null;
    try { sheetEl.releasePointerCapture(id); } catch(e){}
    var v = 0;
    if (samples.length > 1) { var a = samples[0], b = samples[samples.length - 1]; if (b[0] > a[0]) v = (b[1] - a[1]) / ((b[0] - a[0]) / 1000); }
    var proj = sheetY + v * .499;
    if (proj > sheetH * .5 || sheetY > sheetH * .6) spring(sheetH, v, finishClose);
    else spring(0, v, sheetResetStyles);
  }
  sheetEl.addEventListener("pointerdown", function(e){
    if (!sheetEl.classList.contains("show") || reduced() || sheetNotice) return;
    if (e.pointerType === "mouse" && e.button !== 0) return;
    var t = e.target;
    if (t.closest(".sheet-close")) return;
    var inBody = t.closest("#sheetBody");
    if (inBody && (inBody.scrollTop > 0 || t.closest("textarea,input,a,button,summary,select"))) return;
    sheetH = sheetEl.offsetHeight || 1;
    cand = { x: e.clientX, y: e.clientY, id: e.pointerId, body: !!inBody };
  });
  sheetEl.addEventListener("pointermove", function(e){
    if (cand && e.pointerId === cand.id) {
      if (e.pointerType === "mouse" && !(e.buttons & 1)) { cand = null; return; }
      var dy = e.clientY - cand.y, dx = e.clientX - cand.x;
      if (Math.abs(dy) < 8 && Math.abs(dx) < 8) return;                 // hysteresis
      if (Math.abs(dx) > Math.abs(dy) || (cand.body && dy < 0)) { cand = null; return; }
      cancelAnimationFrame(sheetAnim);
      var y0 = curY();                                                   // grab it mid-flight
      sheetEl.style.transition = "none"; scrimEl.style.transition = "none"; setY(y0);
      d = { id: cand.id, sy: e.clientY, y0: y0 }; samples = []; cand = null;
      try { sheetEl.setPointerCapture(e.pointerId); } catch(err){}
      sheetEl.style.userSelect = "none";
    }
    if (d && e.pointerId === d.id) {
      if (e.pointerType === "mouse" && !(e.buttons & 1)) { end(); return; }
      var raw = d.y0 + (e.clientY - d.sy), y = raw < 0 ? -rb(-raw, sheetH) : raw;
      setY(y);
      var now = performance.now(); samples.push([now, y]);
      while (samples.length > 1 && now - samples[0][0] > 100) samples.shift();
    }
  });
  function up(){ cand = null; if (d) { sheetEl.style.userSelect = ""; end(); } }
  sheetEl.addEventListener("pointerup", up); sheetEl.addEventListener("pointercancel", up);
})();

/* ===== UPDATE NOTICES: shared detail/settings sheet ===== */
function closeSheetNotice(){
  if (!sheetNotice) return true;
  if (sheetNotice.kind === 'rendering') return false;
  if (sheetNotice.busy || noticeClosing) return false;
  var notice = sheetNotice, api = bridge();
  if (notice.kind === "update") {
    if (api) api.dismiss_update();
    sheetNotice = null; return true;
  }
  noticeClosing = true;
  var failed = function(){ noticeClosing = false; document.getElementById("noticeStatus").textContent = "Could not remember this notice. Please try closing it again."; };
  try {
    Promise.resolve(api ? api.acknowledge_update(notice.version) : true).then(function(ok){
      noticeClosing = false;
      if (!ok) { failed(); return; }
      sheetNotice = null; hideSheet();
    }, failed);
  } catch(e){ failed(); }
  return false;
}
function canShowNotice(){
  return !(typeof focusSession !== 'undefined' && focusSession) && !(BOOT && BOOT.chooseRendering) && (!EMBEDDED || bridge()) && !sheetEl.classList.contains("show") && !document.getElementById("state-overlay").classList.contains("show");
}
function showUpdatePrompt(info){
  if (sheetNotice && sheetNotice.kind !== "update") return false;
  if (!sheetNotice) {
    if (!canShowNotice()) return false;
    showSheet("Update available", '<div class="detail-block"><p id="noticeStatus" class="detail-desc" role="status" aria-live="polite"></p></div>'+
      '<div class="detail-block"><p>Install the latest version? The app will restart.</p></div>'+
      '<button class="btn-primary" id="updateInstall">Update now</button><button class="btn-secondary" id="updateLater">Not now</button>');
    sheetNotice = {kind:"update"};
    document.getElementById("updateInstall").onclick = function(){
      var api = bridge(); if (!api || sheetNotice.busy) return;
      showUpdatePrompt({text:"Downloading update...",busy:true});
      Promise.resolve(api.install_update()).catch(function(){ showUpdatePrompt({text:"Could not start the update. Please try again.",failed:true}); });
    };
    document.getElementById("updateLater").onclick = hideSheet;
  }
  if (sheetNotice.text === info.text && sheetNotice.busy === !!info.busy && sheetNotice.failed === !!info.failed) return true;
  sheetNotice.text = info.text; sheetNotice.busy = !!info.busy; sheetNotice.failed = !!info.failed;
  document.getElementById("noticeStatus").textContent = info.text || "A new version is available.";
  document.getElementById("updateInstall").textContent = info.failed ? "Try again" : "Update now";
  document.getElementById("updateInstall").style.display = info.busy ? "none" : "";
  document.getElementById("updateLater").style.display = info.busy ? "none" : "";
  document.getElementById("updateLater").textContent = info.failed ? "Close" : "Not now";
  document.getElementById("sheetClose").disabled = !!info.busy;
  sheetEl.setAttribute("aria-busy", info.busy ? "true" : "false");
  return true;
}
function showUpdateFailure(){
  if(!canShowNotice())return false;
  showSheet('Update could not be installed','<div class="detail-block"><p class="detail-desc">The installer did not finish successfully. The app has been reopened. Try the update again, or download the installer from the project’s GitHub Releases page.</p></div><button class="btn-secondary" id="updateFailureClose">Close</button>');
  document.getElementById('updateFailureClose').onclick=hideSheet;
  return true;
}
function releaseNotesHTML(text){
  var html = "", list = false;
  String(text || "No release notes were provided for this version.").split(/\r?\n/).forEach(function(line){
    var bullet = /^\s*[-*+]\s+/.test(line);
    if (list && !bullet) { html += "</ul>"; list = false; }
    var safe = esc(line.replace(/^\s*#{1,6}\s+|^\s*[-*+]\s+/g, "")).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    if (bullet) { if (!list) { html += "<ul>"; list = true; } html += "<li>"+safe+"</li>"; }
    else if (/^\s*#{1,6}\s+/.test(line)) html += "<h4>"+safe+"</h4>";
    else if (line.trim()) html += "<p>"+safe+"</p>";
  });
  return html + (list ? "</ul>" : "");
}
function showReleaseNotes(info){
  if (sheetNotice) return sheetNotice.kind === "release";
  if (!canShowNotice()) return false;
  showSheet("What's new", '<div class="detail-block"><div class="detail-desc">Updated to version '+esc(info.version)+'</div></div>'+
    '<div class="detail-block release-notes">'+releaseNotesHTML(info.notes)+'</div>'+
    '<p id="noticeStatus" role="status" aria-live="polite"></p><button class="btn-primary" id="releaseDone">Got it</button>');
  sheetNotice = {kind:"release",version:info.version};
  document.getElementById("sheetClose").disabled = false;
  sheetEl.removeAttribute("aria-busy");
  document.getElementById("releaseDone").onclick = hideSheet;
  return true;
}

/* undo toast */
var toastTimer = 0, toastUndoFn = null;
function showToast(msg, undo){
  clearTimeout(toastTimer); toastUndoFn = undo || null;
  document.getElementById("toastMsg").textContent = msg;
  var b = document.getElementById("toastUndo"); b.style.display = undo ? "" : "none"; b.tabIndex = 0;
  document.getElementById("toast").classList.add("show");
  toastTimer = setTimeout(hideToast, 5000);
}
function hideToast(){ document.getElementById("toast").classList.remove("show"); document.getElementById("toastUndo").tabIndex = -1; toastUndoFn = null; }
document.getElementById("toastUndo").addEventListener("click", function(){ var f = toastUndoFn; hideToast(); if (f) f(); });

/* ===== SETTINGS ===== */
function currentLevel(){ var l = loadSetting("glassLevel"); return l==null ? 1 : l; }
function renderingMode(){ return loadSetting("renderingMode") === "performance" ? "performance" : "fancy"; }
function renderingOptions(unselected){
  return '<div class="seg-control">'+["performance","fancy"].map(function(m){
    var active = !unselected && renderingMode() === m;
    return '<button class="seg'+(active?' active':'')+'" data-rendering-opt="'+m+'" aria-pressed="'+active+'">'+(m==="performance"?'Performance':'Fancy')+'</button>';
  }).join('')+'</div><div class="detail-desc" style="padding:12px 16px">Performance: light frosted glass and a still background for weaker systems.<br>Fancy: full glass refraction with subtle color dispersion.</div>';
}
function setRenderingMode(mode){
  if (mode !== "performance" && mode !== "fancy") return;
  var buttons = document.querySelectorAll('[data-rendering-opt]'), status = document.getElementById('renderingStatus');
  buttons.forEach(function(b){ b.disabled = true; });
  if (status) status.textContent = '';
  var failed = function(){
    buttons.forEach(function(b){ b.disabled = false; });
    if (status) status.textContent = 'Could not save your choice. Please try again.';
  };
  try {
    var api = bridge(), saved;
    if (EMBEDDED) { if (!api) { failed(); return; } saved = api.save_setting('renderingMode', mode); }
    else { var next = Object.assign({}, SETTINGS, {renderingMode:mode}); localStorage.setItem('planner.settings', JSON.stringify(next)); saved = true; }
    Promise.resolve(saved).then(function(ok){
      if (!ok) { failed(); return; }
      SETTINGS.renderingMode = mode;
      document.documentElement.setAttribute('data-rendering', mode);
      if (LENS.ok) {
        LENS.defs.textContent = ''; LENS.cache = {};
        LENS.seen.forEach(function(el){ el.__lk = null; });
        lensScan();
      }
      buttons.forEach(function(b){ var active = b.dataset.renderingOpt === mode; b.disabled = false; b.classList.toggle('active', active); b.setAttribute('aria-pressed', active); });
      if (BOOT && BOOT.chooseRendering) {
        BOOT.chooseRendering = false; sheetNotice = null;
        document.getElementById('sheetClose').disabled = false;
        document.getElementById('sheetClose').style.display = '';
        hideSheet(); syncNow();
      }
    }, failed);
  } catch(e){ failed(); }
}
function showRenderingChoice(){
  if (!BOOT || !BOOT.chooseRendering || !bridge() || sheetEl.classList.contains('show')) return;
  showSheet('Choose your rendering mode', '<div class="detail-list">'+renderingOptions(true)+'</div><div class="detail-block"><p>You can always change this in Settings.</p><p id="renderingStatus" role="status" aria-live="polite"></p></div>');
  sheetNotice = {kind:'rendering'};
  document.getElementById('sheetClose').disabled = true;
  document.getElementById('sheetClose').style.display = 'none';
}

async function refreshDateChecker(){
  var status = document.getElementById('dateCheckerStatus'); if (!status) return;
  try {
    var api = bridge();
    if (!api) throw new Error('Date checking settings are available in the desktop app.');
    var state = await api.date_checker_state();
    if (!status.isConnected) return;
    if (state.error) throw new Error(state.error);
    SETTINGS.dateChecker = state.mode;
    document.querySelectorAll('[data-date-checker]').forEach(function(button){
      var active = button.dataset.dateChecker === state.mode;
      button.disabled = button.dataset.dateChecker === 'gemini' && !state.geminiAvailable;
      button.classList.toggle('active',active); button.setAttribute('aria-pressed',active);
    });
    status.textContent = state.geminiAvailable?'Used the next time you sync. Local stays on this computer; Gemini sends date-checking text to Gemini.':'Local is always used without a Gemini API key. Add a key through Change login info to enable Gemini.';
  } catch(e) {if (status.isConnected) status.textContent = e.message||'Could not load date checker settings.';}
}
async function setDateChecker(mode){
  var status = document.getElementById('dateCheckerStatus'), api = bridge(); if (!status || !api) return;
  document.querySelectorAll('[data-date-checker]').forEach(function(button){button.disabled=true;});
  try {
    var saved = await api.save_setting('dateChecker',mode);
    await refreshDateChecker();
    if (!saved && status.isConnected) status.textContent = 'Could not save this choice. Check your Gemini key or try again.';
  } catch(e) {
    await refreshDateChecker();
    if (status.isConnected) status.textContent = 'Could not save this choice. Please try again.';
  }
}
function syncDiagnosticsText(){
  var diagnostics=DATA.diagnostics||{}, planner=diagnostics.planner||{}, sources={};
  ['legacy','planner','timetable'].forEach(function(name){
    var source=(planner.sources||{})[name];if(!source)return;
    var clean={};
    ['status','error'].forEach(function(key){if(typeof source[key]==='string')clean[key]=source[key].slice(0,80);});
    ['received','parsed','skipped','ignored_free_days'].forEach(function(key){if(Number.isFinite(source[key]))clean[key]=source[key];});
    clean.schema_errors=(source.schema_errors||[]).slice(0,12).map(function(item){return {field:String(item.field||'').slice(0,120),type:String(item.type||'').slice(0,80)};});
    clean.skipped_records=(Array.isArray(source.skipped_records)?source.skipped_records:[]).slice(0,12).map(function(item){
      item=item||{};
      return {date:typeof item.date==='string' && /^\d{4}-\d{2}-\d{2}$/.test(item.date)?item.date:'unknown',
        start:typeof item.start==='string' && /^\d{2}:\d{2}$/.test(item.start)?item.start:'unknown',
        event_type:typeof item.event_type==='string' && /^[a-z][a-z0-9-]{0,47}$/.test(item.event_type)?item.event_type:'unknown'};
    });
    sources[name]=clean;
  });
  function events(days){return (days||[]).reduce(function(total,day){return total+(day.events||[]).length;},0);}
  return JSON.stringify({report:'Smartschool Planner sync diagnostics',version:diagnostics.app_version||'Unknown (sync with updated app)',
    counts:{schedule:events(DATA.days),timetable:events(DATA.all_classes),tasks:(DATA.todos||[]).length},
    plannerDiagnosticsAvailable:!!diagnostics.planner,sources:sources},null,2);
}
async function copySyncDiagnostics(button){
  button.disabled=true;
  var report=document.getElementById('syncDiagnosticsReport'), status=document.getElementById('syncDiagnosticsStatus');
  report.value=syncDiagnosticsText();report.hidden=false;
  try {
    if(navigator.clipboard && navigator.clipboard.writeText)await navigator.clipboard.writeText(report.value);
    else {report.focus();report.select();if(!document.execCommand('copy'))throw new Error('copy');}
    status.textContent='Copied. You can paste this report into a support message.';
  } catch(e) {
    if(report.isConnected){report.focus();report.select();status.textContent='Copy was unavailable. Select and copy the report below.';}
  } finally {button.disabled=false;}
}
function openSettings(){
  var st = document.documentElement.getAttribute("data-style") || "vivid";
  var body =
    '<div class="setting-group"><h4>Date checker</h4><div class="detail-list"><div class="seg-control"><button class="seg active" data-date-checker="local" aria-pressed="true" disabled>Local</button><button class="seg" data-date-checker="gemini" aria-pressed="false" disabled>Gemini</button></div><p class="detail-desc" id="dateCheckerStatus" role="status" aria-live="polite" style="padding:12px 16px">Checking available date checkers...</p></div></div>'+
    '<div class="setting-group"><h4>Rendering</h4><div class="detail-list">'+renderingOptions()+'</div><p id="renderingStatus" role="status" aria-live="polite"></p></div>'+
    '<div class="setting-group"><h4>Theme</h4><div class="detail-list"><div class="seg-control">'+
      '<button class="seg'+(st==="vivid"?" active":"")+'" data-style-opt="vivid">Vivid</button>'+
      '<button class="seg'+(st==="clear"?" active":"")+'" data-style-opt="clear">Clear</button></div></div></div>'+
    '<div class="setting-group"><h4>Mode</h4><div class="detail-list"><div class="seg-control">'+
      ["auto","light","dark"].map(function(m){ return '<button class="seg'+((loadSetting("scheme")||"auto")===m?" active":"")+'" data-scheme-opt="'+m+'">'+m.charAt(0).toUpperCase()+m.slice(1)+'</button>'; }).join("")+'</div></div></div>'+
    '<div class="setting-group"><h4>Liquid glass</h4><div class="detail-list"><div style="padding:14px 16px">'+
      '<input type="range" min="0" max="2" step="1" value="'+currentLevel()+'" class="glass-slider" id="glassSlider" aria-label="Liquid glass strength">'+
      '<div class="glass-level-labels"><span>Subtle</span><span>Balanced</span><span>Strong</span></div></div></div></div>'+
    '<div class="setting-group"><h4>Text size</h4><div class="detail-list"><div class="seg-control">'+
      [["s","Small"],["m","Default"],["l","Large"]].map(function(o){ return '<button class="seg'+((loadSetting("textSize")||"m")===o[0]?" active":"")+'" data-text-opt="'+o[0]+'">'+o[1]+'</button>'; }).join("")+'</div></div></div>'+
    '<div class="setting-group"><h4>Accessibility</h4><div class="detail-list"><div class="setting-row"><span>Reduce motion</span><div class="toggle'+(loadSetting("reduceMotion")?" on":"")+'" id="motionToggle" role="switch" tabindex="0" aria-label="Reduce motion" aria-checked="'+(loadSetting("reduceMotion")?"true":"false")+'"></div></div>'+
      '<div class="setting-row"><span>Animated background (Fancy)</span><div class="toggle'+(loadSetting("animatedBg")===false?"":" on")+'" id="bgToggle" role="switch" tabindex="0" aria-label="Animated background (Fancy)" aria-checked="'+(loadSetting("animatedBg")===false?"false":"true")+'"></div></div></div></div>'+
    (DATA.main_url ? '<div class="setting-group"><h4>Account</h4><div class="detail-list">'+rows([["School",DATA.main_url]])+'</div></div>'+
    '<button class="btn-primary" data-external="1">'+ICON.ext+' Open in Smartschool</button>' : "");
  if (EMBEDDED) body += '<div class="setting-group"><button class="btn-secondary" data-change-login="1">Change login info</button></div>';
  body += '<div class="setting-group"><h4>Sync support</h4><button class="btn-secondary" data-copy-sync-diagnostics>Copy sync diagnostics</button><p class="detail-desc" id="syncDiagnosticsStatus" role="status">Copies counts, technical error fields, and dates, start times and event types for up to 12 skipped entries per source. No login details, school address, lesson text or LVS content.</p><textarea id="syncDiagnosticsReport" class="note-area" aria-label="Sync diagnostics report" readonly hidden spellcheck="false"></textarea></div>';
  var rebuilt = showSheet("Settings", body, null, true);
  refreshDateChecker();
  if (!rebuilt) return;
  var slider = document.getElementById("glassSlider");
  slider.addEventListener("input", async function(){ var v = parseInt(slider.value,10); applyGlassLevel(v); if(!await saveSetting("glassLevel", v)){slider.value=currentLevel();applyGlassLevel(currentLevel());} });
  var tog = document.getElementById("motionToggle");
  tog.addEventListener("click", async function(){ var on = !tog.classList.contains("on"); if(!await saveSetting("reduceMotion", on))return; tog.classList.toggle("on", on); document.body.classList.toggle("reduce-motion", on); tog.setAttribute("aria-checked", on); });
  var bgt = document.getElementById("bgToggle");
  bgt.addEventListener("click", async function(){ var on = !bgt.classList.contains("on"); if(!await saveSetting("animatedBg", on))return; bgt.classList.toggle("on", on); document.body.classList.toggle("static-bg", !on); bgt.setAttribute("aria-checked", on); });
  Array.prototype.forEach.call(document.querySelectorAll("#sheetBody .toggle"), function(el){ el.addEventListener("keydown", function(e){ if (e.key === " " || e.key === "Enter") { e.preventDefault(); el.click(); } }); });
}

function applyScheme(){
  var m = loadSetting("scheme");
  var light = m === "light" || (m !== "dark" && matchMedia("(prefers-color-scheme: light)").matches);
  document.documentElement.setAttribute("data-scheme", light ? "light" : "dark");
  applyGlassLevel(currentLevel());
}
async function setTextSize(v){
  if(!await saveSetting("textSize", v))return;
  if (v === "s" || v === "l") document.documentElement.setAttribute("data-text", v); else document.documentElement.removeAttribute("data-text");
  document.querySelectorAll("[data-text-opt]").forEach(function(el){ el.classList.toggle("active", el.dataset.textOpt === v); });
}
async function setScheme(m){
  if(!await saveSetting("scheme", m))return;
  noTrans(applyScheme);
  document.querySelectorAll("[data-scheme-opt]").forEach(function(el){ el.classList.toggle("active", el.dataset.schemeOpt === m); });
}
function noTrans(fn){ var r = document.documentElement; r.classList.add("no-trans"); fn(); void r.offsetHeight; requestAnimationFrame(function(){ requestAnimationFrame(function(){ r.classList.remove("no-trans"); }); }); }
async function setStyle(style){
  if(!await saveSetting("style", style))return;
  noTrans(function(){
    document.documentElement.setAttribute("data-style", style);
    applyGlassLevel(currentLevel());
    document.querySelectorAll("[data-style-opt]").forEach(function(el){ el.classList.toggle("active", el.dataset.styleOpt===style); });
  });
}

function applyGlassLevel(level){
  var isClear = document.documentElement.getAttribute("data-style")==="clear";
  var light = document.documentElement.getAttribute("data-scheme")==="light";
  var vivid = [{op:.32,blur:30,sat:180,spec:1},{op:.55,blur:26,sat:170,spec:.9},{op:.78,blur:22,sat:160,spec:.7}];
  var clear = [{op:.06,blur:14,sat:135,spec:1},{op:.12,blur:18,sat:140,spec:1},{op:.24,blur:22,sat:150,spec:.9}];
  var set = isClear ? clear : vivid;
  var m = set[level] || set[1];
  var r = document.documentElement.style;
  r.setProperty("--glass-opacity", m.op);
  r.setProperty("--glass-blur", m.blur+"px");
  r.setProperty("--glass-saturate", m.sat+"%");
  r.setProperty("--glass-specular", m.spec);
  r.setProperty("--glass-tint-dark", isClear ? (light ? "255, 255, 255" : "10, 18, 30") : (light ? "255, 255, 255" : "18, 18, 28"));
}

/* ===== LOADING / ERROR ===== */
function showLoading(label){
  if (focusSession) {document.getElementById('focusStatus').textContent = label||'Syncing...'; return;}
  document.getElementById("stateContent").innerHTML = '<div class="state-spinner"></div><div style="font-size:17px;font-weight:600">'+esc(label||"Syncing...")+'</div><div class="skeleton-group"><div class="skel"></div><div class="skel"></div><div class="skel"></div></div>';
  var ov0 = document.getElementById("state-overlay");
  ov0.setAttribute("role","status"); ov0.removeAttribute("aria-modal"); ov0.removeAttribute("aria-labelledby");
  ov0.classList.add("show");
}
function showError(info){
  if (typeof info === "string") info = {title:"Could not sync", message:info};
  info = info || {};
  var kind = info.kind || "unknown";
  var canFix = kind === "login" || kind === "config";
  var h = '<div class="error-icon">'+ICON.warn+'</div><div class="error-title" id="errTitle">'+esc(info.title||"Could not sync")+'</div>'
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
  var ov = document.getElementById("state-overlay");
  if (!ov.classList.contains("show")) ovRet = document.activeElement;
  ov.setAttribute("role","alertdialog"); ov.setAttribute("aria-modal","true"); ov.setAttribute("aria-labelledby","errTitle");
  ov.classList.add("show");
  var f1 = document.getElementById("fixBtn") || document.getElementById("retryBtn"); if (f1) f1.focus({preventScroll:true});
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
var ovRet = null;
function hideState(){ document.getElementById("state-overlay").classList.remove("show"); if (ovRet && document.body.contains(ovRet) && ovRet.focus) ovRet.focus({preventScroll:true}); ovRet = null; }

/* ===== EVENTS ===== */
var tabScrubAt = 0;
function selectTab(name){
  var prevI = TABS.indexOf(activeTab); activeTab = name; activeCourse = "All"; activeType = '';
  var s = document.getElementById("scroll"); s.style.scrollBehavior = "auto"; s.scrollTop = 0; s.style.scrollBehavior = "";
  render(DATA, COMPLETED);
  var ni = TABS.indexOf(activeTab);
  if (ni !== prevI) { s.style.setProperty("--dx", (ni > prevI ? 14 : -14) + "px"); s.classList.remove("tab-in"); void s.offsetWidth; s.classList.add("tab-in"); }
}
document.getElementById("tabbar").addEventListener("click", function(e){
  if (performance.now() - tabScrubAt < 120) return;
  var tab = e.target.closest(".tab"); if (!tab) return;
  selectTab(tab.dataset.tab);
});
/* slide your finger (or mouse) across the bar: the bubble follows, release selects */
(function(){
  var bar = document.getElementById("tabbar"), bub = document.getElementById("bubble"), st = null;
  function geom(){ var r = bar.getBoundingClientRect(); return { left: r.left + 10, w: (r.width - 20) / TABS.length }; }
  function idxAt(x, g){ return Math.max(0, Math.min(TABS.length - 1, Math.floor((x - g.left) / g.w))); }
  function peek(i){ document.querySelectorAll(".tab").forEach(function(t, k){ t.classList.toggle("peek", k === i); }); }
  function stop(){ bar.classList.remove("scrubbing"); peek(-1); st = null; }
  bar.addEventListener("pointerdown", function(e){
    if (e.pointerType === "mouse" && e.button !== 0) return;
    st = { id: e.pointerId, x0: e.clientX, g: geom(), moving: false, peek: -1 };
  });
  bar.addEventListener("pointermove", function(e){
    if (!st || e.pointerId !== st.id) return;
    if (e.pointerType === "mouse" && !(e.buttons & 1)) { stop(); updateTabs(); return; }
    if (!st.moving) {
      if (Math.abs(e.clientX - st.x0) < 6) return;
      st.moving = true; bar.classList.add("scrubbing");
      try { bar.setPointerCapture(e.pointerId); } catch(err){}
    }
    var g = st.g, x = e.clientX - g.w / 2 - g.left, max = g.w * (TABS.length - 1);
    bub.style.transform = "translateX(" + Math.max(-10, Math.min(max + 10, x)) + "px)";
    var i = idxAt(e.clientX, g); if (i !== st.peek) { st.peek = i; peek(i); }
  });
  function up(e){
    if (!st || e.pointerId !== st.id) return;
    var moved = st.moving, i = idxAt(e.clientX, st.g);
    try { bar.releasePointerCapture(e.pointerId); } catch(err){}
    stop();
    if (moved) { tabScrubAt = performance.now(); if (TABS[i] !== activeTab) selectTab(TABS[i]); else updateTabs(); }
  }
  bar.addEventListener("pointerup", up);
  bar.addEventListener("pointercancel", function(e){ if (st && e.pointerId === st.id) { stop(); updateTabs(); } });
  bar.addEventListener("keydown", function(e){
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    var tabs = Array.prototype.slice.call(document.querySelectorAll(".tab")), k = tabs.indexOf(document.activeElement);
    if (k < 0) return; e.preventDefault();
    tabs[(k + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length].focus();
  });
})();
(function(){
  var ch = document.getElementById("chips"), drag = null, moved = false;
  ch.addEventListener("wheel", function(e){
    if (ch.scrollWidth <= ch.clientWidth) return;
    ch.scrollLeft += Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY; e.preventDefault();
  }, { passive: false });
  ch.addEventListener("pointerdown", function(e){ if (e.target.closest('select') || e.pointerType !== "mouse" || e.button !== 0) return; drag = { x: e.clientX, left: ch.scrollLeft }; moved = false; });
  window.addEventListener("pointermove", function(e){ if (!drag) return; var dx = e.clientX - drag.x; if (!moved && Math.abs(dx) < 6) return; moved = true; ch.scrollLeft = drag.left - dx; });
  window.addEventListener("pointerup", function(){ drag = null; });
  ch.addEventListener("click", function(e){ if (moved) { e.stopPropagation(); e.preventDefault(); moved = false; } }, true);
})();
document.getElementById("chips").addEventListener("click", function(e){
  if(e.target.closest('#taskTypeFilter')){
    if(typeMenu && typeMenu.classList.contains('open'))closeTypeMenu(true);else openTypeMenu(e.detail===0,false);
    return;
  }
  var c = e.target.closest("[data-course]"); if (!c) return;
  activeCourse = c.dataset.course; render(DATA, COMPLETED);
});
document.getElementById('chips').addEventListener('keydown',function(e){
  if(e.target.id==='taskTypeFilter' && (e.key==='ArrowDown'||e.key==='ArrowUp')){e.preventDefault();openTypeMenu(true,e.key==='ArrowUp');}
});
document.addEventListener('keydown',function(e){
  if(e.key==='Escape' && typeMenu && typeMenu.classList.contains('open')){e.preventDefault();e.stopImmediatePropagation();closeTypeMenu(true);}
},true);
document.addEventListener('pointerdown',function(e){
  if(typeMenu && !typeMenu.contains(e.target) && !e.target.closest('#taskTypeFilter'))closeTypeMenu(false);
});
document.addEventListener('focusin',function(e){if(typeMenu && !typeMenu.contains(e.target) && e.target.id!=='taskTypeFilter')closeTypeMenu(false);});
document.addEventListener('scroll',function(e){if(!typeMenu || e.target!==typeMenu)closeTypeMenu(false);},true);
window.addEventListener('resize',function(){closeTypeMenu(true);});
document.getElementById("syncBtn").addEventListener("click", function(){
  var icon = document.getElementById("syncIcon"), sb = document.getElementById("syncBtn"); icon.classList.add("sync-spin"); sb.setAttribute("aria-busy","true"); syncNow();
  setTimeout(function(){ icon.classList.remove("sync-spin"); sb.removeAttribute("aria-busy"); }, 2000);
});
document.getElementById("settingsBtn").addEventListener("click", openSettings);

/* search */
function openSearch(){ document.getElementById("searchBtn").setAttribute("aria-expanded","true"); document.body.classList.add("searching"); var i = document.getElementById("searchInput"); i.focus(); i.select(); }
function closeSearch(){
  document.getElementById("searchBtn").setAttribute("aria-expanded","false");
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
document.getElementById("scroll").addEventListener("click", async function(e){
  var readAll=e.target.closest('[data-lvs-read-all]');if(readAll){markAllLvsRead(readAll);return;}
  var absence=e.target.closest('[data-lvs-absence]');if(absence){openLvsAbsence(absence.dataset.lvsAbsence);return;}
  var note = e.target.closest('[data-lvs-note]'); if (note) {openLvsNote(note.dataset.lvsNote); return;}
  var focus = e.target.closest('[data-focus-id]');
  if (focus) {e.stopPropagation(); openTask(focus.dataset.focusId,true); return;}
  if (e.target.closest("[data-sync-now]")) { syncNow(); return; }
  var pin = e.target.closest("[data-pin]");
  if (pin) { e.stopPropagation(); await togglePin(pin.dataset.pin); render(DATA, COMPLETED, { keepScroll: true }); return; }
  if (e.target.closest("[data-toggle-completed]")) { completedOpen = !completedOpen; render(DATA, COMPLETED, { keepScroll: true }); return; }
  var chk = e.target.closest("[data-check]");
  if (chk) {
    e.stopPropagation();
    var id = chk.dataset.check, now = COMPLETED.indexOf(id)===-1, row = chk.closest(".task-row");
    if (now && row && (activeTab==="todo" || activeTab==="missed")) { chk.classList.add("done"); row.classList.add("leaving"); setTimeout(async function(){ if(await markTask(id, true))showToast("Marked as done", function(){ markTask(id, false); }); }, 260); }
    else { var saved=await markTask(id, now); if (saved && now) showToast("Marked as done", function(){ markTask(id, false); }); }
    return;
  }
  var td = e.target.closest("[data-detail='task']"); if (td) { openTask(td.dataset.id); return; }
  var ld = e.target.closest("[data-detail='lesson']"); if (ld) { openLesson(ld.dataset.moment); return; }
  var gd = e.target.closest("[data-detail='grade']"); if (gd) { openGrade(gd.dataset.id); }
});
document.getElementById("sheetBody").addEventListener("input", function(e){
  if (e.target.id !== "noteArea") return;
  if (noteTimer) clearTimeout(noteTimer);
  noteTimer = setTimeout(flushNote, 500);
});
document.getElementById("sheetBody").addEventListener("click", async function(e){
  var diagnostics=e.target.closest('[data-copy-sync-diagnostics]');if(diagnostics){copySyncDiagnostics(diagnostics);return;}
  var checker = e.target.closest('[data-date-checker]'); if (checker) {setDateChecker(checker.dataset.dateChecker); return;}
  if (e.target.closest('[data-change-login]')) {
    var api = bridge();
    if (api && api.open_setup) {
      if(!await flushNote())return;
      await hideSheet(); showLoading('Waiting for login details...');
      Promise.resolve(api.open_setup()).catch(function(){hideState();showToast('Could not open login settings. Please try again.');});
    }
    return;
  }
  var note = e.target.closest('[data-lvs-note]'); if (note) {openLvsNote(note.dataset.lvsNote); return;}
  if (e.target.closest('[data-focus-task]')) {focusAction('start'); return;}
  var ou = e.target.closest("[data-open-url]"); if (ou) { openExternal(ou.getAttribute("data-open-url")); return; }
  var ps = e.target.closest("[data-pin-sheet]");
  if (ps) {
    var on = await togglePin(ps.dataset.pinSheet); if(on===null)return;
    ps.lastChild.textContent = on ? " Unpin from top" : " Pin to top";
    render(DATA, COMPLETED, { keepScroll: true });
    return;
  }
  if (e.target.closest("[data-external]")) { openSmartschool(); return; }
  var so = e.target.closest("[data-style-opt]"); if (so) { setStyle(so.dataset.styleOpt); return; }
  var rm = e.target.closest("[data-rendering-opt]"); if (rm) { setRenderingMode(rm.dataset.renderingOpt); return; }
  var sm = e.target.closest("[data-scheme-opt]"); if (sm) { setScheme(sm.dataset.schemeOpt); return; }
  var tx = e.target.closest("[data-text-opt]"); if (tx) { setTextSize(tx.dataset.textOpt); return; }
  var td = e.target.closest("[data-detail='task']"); if (td) { openTask(td.dataset.id); }
});
document.getElementById("scroll").addEventListener("keydown", function(e){
  if (e.key !== "Enter" && e.key !== " ") return;
  var t = e.target;
  if (t.matches(".check,.grade-row")) { e.preventDefault(); t.click(); }
  else if (t.matches(".task-body,.lesson-body")) { e.preventDefault(); t.closest("[data-detail]").click(); }
});
document.getElementById("scroll").addEventListener("scroll", function(){
  var hd = document.getElementById("header"), tp = document.getElementById("top"), on = tp.classList.contains("scrolled"), top = this.scrollTop;
  if (!on && top > 10) { hd.classList.add("scrolled"); tp.classList.add("scrolled"); } else if (on && top < 3) { hd.classList.remove("scrolled"); tp.classList.remove("scrolled"); }
});
(function(){
  var tp = document.getElementById("top");
  var hd0 = document.getElementById("header");
  function m(){ var r = document.documentElement.style; r.setProperty("--topH", tp.offsetHeight + "px"); r.setProperty("--hdrH", hd0.offsetHeight + "px"); }
  m(); if (window.ResizeObserver) { var ro = new ResizeObserver(m); ro.observe(tp); ro.observe(hd0); } else window.addEventListener("resize", m);
})();
document.addEventListener("visibilitychange", function(){
  document.body.classList.toggle("page-hidden", document.hidden);
});
matchMedia("(prefers-color-scheme: light)").addEventListener("change", applyScheme);
window.addEventListener("blur", function(){ document.body.classList.add("inactive"); });
window.addEventListener("focus", function(){ document.body.classList.remove("inactive"); });

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
    var compact = !!focusSession;
    var dx = 0, dy = 0, start = null, busy = false, lastW = 0, lastH = 0, MIN_W = compact?360:760, MIN_H = compact?420:560;
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

/* ===== LIQUID GLASS REFRACTION: the backdrop is bent at the glass edge (SVG displacement map) with slight colour dispersion ===== */
var LENS = { ok: false, n: 0, cache: {}, seen: null, ro: null, defs: null };
(function(){
  try { LENS.ok = !!(window.CSS && CSS.supports && CSS.supports("backdrop-filter", "url(#a)") && window.WeakSet && window.ResizeObserver) && !matchMedia("(prefers-reduced-transparency:reduce)").matches; } catch(e){}
  if (!LENS.ok) return;
  var NS = "http://www.w3.org/2000/svg", svg = document.createElementNS(NS, "svg");
  svg.setAttribute("width", "0"); svg.setAttribute("height", "0"); svg.setAttribute("aria-hidden", "true"); svg.style.cssText = "position:absolute;pointer-events:none";
  LENS.defs = document.createElementNS(NS, "defs"); svg.appendChild(LENS.defs); document.body.appendChild(svg);
  LENS.seen = new Set();
  LENS.q = new Set(); LENS.flush = function(){ lensApplyBatch(Array.from(LENS.q)); LENS.q.clear(); };
  LENS.ro = new ResizeObserver(function(es){
    var resizing = document.body.classList.contains("resizing"), ready = [];
    es.forEach(function(e){ if (!LENS.seen.has(e.target)) return; if (resizing) LENS.q.add(e.target); else ready.push(e.target); });
    lensApplyBatch(ready);
  });
})();
function lensMapURL(w, h, r, bezel){
  var c = document.createElement("canvas"); c.width = w; c.height = h;
  var x = c.getContext("2d"), img = x.createImageData(w, h), d = img.data, hw = w / 2, hh = h / 2;
  // The interior is neutral; calculate displacement only around the unchanged glass edge.
  var inset = Math.ceil(r + bezel), skipInterior = w > 2 * inset && h > 2 * inset;
  if (skipInterior) { d.fill(128); for (var a = 3; a < d.length; a += 4) d[a] = 255; }
  for (var j = 0; j < h; j++) for (var i = 0; i < w; i++) {
    if (skipInterior && j >= inset && j < h - inset && i === inset) i = w - inset;
    var px = i + .5 - hw, py = j + .5 - hh, qx = Math.abs(px) - (hw - r), qy = Math.abs(py) - (hh - r);
    var ox = Math.max(qx, 0), oy = Math.max(qy, 0), depth = -((ox || oy ? Math.hypot(ox, oy) : 0) + Math.min(Math.max(qx, qy), 0) - r), k = (j * w + i) * 4, dx = 0, dy = 0;
    if (depth > 0 && depth < bezel) {
      var mag = Math.pow(1 - depth / bezel, 2.2), nx, ny;
      if (qx > 0 || qy > 0) { nx = (px < 0 ? -ox : ox); ny = (py < 0 ? -oy : oy); var L = Math.hypot(nx, ny) || 1; nx /= L; ny /= L; }
      else if (qx > qy) { nx = px < 0 ? -1 : 1; ny = 0; } else { nx = 0; ny = py < 0 ? -1 : 1; }
      dx = -nx * mag; dy = -ny * mag;
    }
    d[k] = Math.round(128 + dx * 127); d[k + 1] = Math.round(128 + dy * 127); d[k + 2] = 128; d[k + 3] = 255;
  }
  x.putImageData(img, 0, 0); return c.toDataURL();
}
function lensFilterId(w, h, r){
  var bezel = Math.max(6, Math.min(r * .8, 26)), shift = Math.min(12, bezel * .5), key = [w, h, Math.round(r)].join("_");
  if (LENS.cache[key]) return LENS.cache[key];
  var id = "lens" + (++LENS.n), cm = { R: "1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0 1", G: "0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 0 1", B: "0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 0 1" };
  var f = '<filter xmlns="http://www.w3.org/2000/svg" id="' + id + '" filterUnits="userSpaceOnUse" x="0" y="0" width="' + w + '" height="' + h + '" color-interpolation-filters="sRGB">' +
    '<feImage href="' + lensMapURL(w, h, r, bezel) + '" x="0" y="0" width="' + w + '" height="' + h + '" preserveAspectRatio="none" result="m"/>';
  [["a", "R", 1], ["b", "G", .93], ["c", "B", .86]].forEach(function(t){
      f += '<feDisplacementMap in="SourceGraphic" in2="m" scale="' + (shift * 2 * t[2]) + '" xChannelSelector="R" yChannelSelector="G" result="d' + t[0] + '"/>' +
           '<feColorMatrix in="d' + t[0] + '" type="matrix" values="' + cm[t[1]] + '" result="' + t[1] + '"/>';
  });
  f += '<feBlend in="R" in2="G" mode="lighten" result="rg"/><feBlend in="rg" in2="B" mode="lighten"/></filter>';
  var holder = document.createElementNS("http://www.w3.org/2000/svg", "svg"); holder.innerHTML = f;
  LENS.defs.appendChild(holder.firstChild);
  LENS.cache[key] = id; return id;
}
var LENS_SEL = [[".app-bar", .6], [".chip", .5], [".icon-btn", .45], ["#sheet", .7], [".type-menu", .5], [".app-bar .bubble", .2]];
function lensMeasure(el){
  var w = el.offsetWidth, h = el.offsetHeight;
  if (el.__r === undefined) el.__r = parseFloat(getComputedStyle(el).borderTopLeftRadius) || 0;
  return { el: el, w: w, h: h, r: Math.min(el.__r, w / 2, h / 2) };
}
function lensApplyBatch(elements){
  if (renderingMode() === 'performance') return;
  // Read every size before applying filters: style writes must not interrupt layout reads.
  elements.map(lensMeasure).forEach(function(size){ lensApply(size.el, size); });
  lensPrune();
}
function lensPrune(){
  var keys = Object.keys(LENS.cache), remaining = keys.length;
  if (remaining <= 32) return;
  var active = new Set();
  LENS.seen.forEach(function(el){ if (el.__lk) active.add(el.__lk.split("|")[0]); });
  keys.forEach(function(key){
    var id = LENS.cache[key];
    if (remaining <= 32 || active.has(id)) return;
    var filter = document.getElementById(id); if (filter) filter.remove();
    delete LENS.cache[key]; remaining--;
  });
}
function lensApply(el, size){
  if (!LENS.ok || renderingMode() === 'performance') return;
  size = size || lensMeasure(el);
  var w = size.w, h = size.h; if (w < 24 || h < 24) return;
  var id = lensFilterId(w, h, size.r), k = id + "|" + el.__lf;
  if (el.__lk === k) return; el.__lk = k;
  var v = "url(#" + id + ") blur(calc(var(--glass-blur) * " + el.__lf + ")) saturate(var(--glass-saturate))";
  el.style.backdropFilter = v; el.style.webkitBackdropFilter = v;
}
function lensScan(){
  if (!LENS.ok) return;
  if (renderingMode() === 'performance') {
    LENS.seen.forEach(function(el){
      el.style.backdropFilter = ''; el.style.webkitBackdropFilter = ''; el.__lk = null;
      LENS.ro.unobserve(el);
    });
    LENS.seen.clear(); LENS.q.clear();
    return;
  }
  var next = new Set(), elements = [];
  LENS_SEL.forEach(function(p){
    var list = document.querySelectorAll(p[0]);
    for (var i = 0; i < list.length; i++) { var el = list[i]; el.__lf = p[1]; next.add(el); elements.push(el); if (!LENS.seen.has(el)) LENS.ro.observe(el); }
  });
  LENS.seen.forEach(function(el){ if (!next.has(el)) { LENS.ro.unobserve(el); LENS.q.delete(el); } });
  LENS.seen = next;
  lensApplyBatch(elements);
}
var _renderLens = render; render = function(){ var r = _renderLens.apply(this, arguments); lensScan(); return r; };
lensScan();

(function(){ var t = 0, b = document.body;
  window.addEventListener("resize", function(){ b.classList.add("resizing"); clearTimeout(t); t = setTimeout(function(){ b.classList.remove("resizing"); if (LENS.flush) LENS.flush(); }, 160); });
})();

/* ===== INIT ===== */
(function(){
  var ttl = document.getElementById("title"); ttl.setAttribute("role","heading"); ttl.setAttribute("aria-level","1");
  document.getElementById("searchInput").setAttribute("aria-label","Search");
  var ts0 = loadSetting("textSize"); if (ts0 === "s" || ts0 === "l") document.documentElement.setAttribute("data-text", ts0);
  var st = loadSetting("style"); if (st === "frost") { st = "clear"; saveSetting("style", "clear"); }
  if (st === "vivid" || st === "clear") document.documentElement.setAttribute("data-style", st);
  if (loadSetting("reduceMotion")) document.body.classList.add("reduce-motion");
  if (!EMBEDDED) document.getElementById("syncBtn").style.display = "none";
  if (EMBEDDED) {
    document.body.classList.add("framed");
    var _m = winCall("win_is_maximized");
    if (_m) Promise.resolve(_m).then(function(v){ document.body.classList.toggle("maximized", !!v); });
  }
  if (loadSetting("animatedBg") === false) document.body.classList.add("static-bg");
  applyScheme();
  restoreFocusSession();
  if (BOOT && BOOT.mode === "loading") { showLoading(BOOT.label); return; }
  if (BOOT && BOOT.mode === "error") { showError(BOOT.error || BOOT.message); return; }
  render(DATA, COMPLETED);
  showRenderingChoice();
  window.addEventListener('pywebviewready', showRenderingChoice);
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
_PLACEHOLDER_RE = re.compile(
    r"__WC_VARS__|__EMBEDDED_JSON__|__BOOT_JSON__|__DATA_JSON__|"
    r"__COMPLETED_JSON__|__SETTINGS_JSON__|__PINNED_JSON__|__NOTES_JSON__"
)


def _build(data, completed_ids, embedded, settings, boot, pinned=None, notes=None) -> str:
    values = {
        "__WC_VARS__": _window_button_css(),
        "__EMBEDDED_JSON__": "true" if embedded else "false",
        "__BOOT_JSON__": _json(boot),
        "__DATA_JSON__": _json(data),
        "__COMPLETED_JSON__": _json(list(completed_ids)),
        "__SETTINGS_JSON__": _json(settings or {}),
        "__PINNED_JSON__": _json(list(pinned or [])),
        "__NOTES_JSON__": _json(notes or {}),
    }
    return _PLACEHOLDER_RE.sub(lambda match: values[match.group(0)], TEMPLATE)


def render_html(
    data: dict,
    completed_ids,
    embedded: bool,
    settings: dict | None = None,
    pinned=None,
    notes: dict | None = None,
    choose_rendering: bool = False,
) -> str:
    return _build(data, completed_ids, embedded, settings, {"chooseRendering": True} if choose_rendering else None, pinned, notes)


def render_loading(settings: dict | None = None, label: str = "Syncing...") -> str:
    return _build(_EMPTY_DATA, [], True, settings, {"mode": "loading", "label": label})


def render_error(info, settings: dict | None = None) -> str:
    """info: a message string, or a dict with kind/title/message/hint/details (see app_errors.explain)."""
    if isinstance(info, str):
        info = {"kind": "unknown", "title": "Could not sync", "message": info}
    return _build(_EMPTY_DATA, [], True, settings, {"mode": "error", "error": info, "message": info.get("message", "")})
