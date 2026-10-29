# Floating controls and menu transition — 2026-10-27

Sources read using Scrapling (HTTP for transcripts/repositories, browser fetch
for Apple's JavaScript documentation):

- [Apple: Meet Liquid Glass](https://developer.apple.com/videos/play/wwdc2025/219/)
  describes controls transforming together with their material, and adapting
  optical properties to the content they present.
- [Apple: Applying Liquid Glass to custom views](https://developer.apple.com/documentation/swiftui/applying-liquid-glass-to-custom-views)
  distinguishes geometry matching from materializing a new surface.
- [liquid-glass-js](https://github.com/Amir-Abushanab/liquid-glass-js)
  demonstrates materialization through changing optics and an unfolding menu.
- [liquid-taffy](https://github.com/arknow91/liquid-taffy)
  explores anchored and button-to-menu expansion with spring motion.

These are design references. No code or dependencies were imported from the two
web experiments. This QML implementation approximates the behavior; it does not
use Apple's proprietary renderer.

## Comparison in the native prototype

Three isolated QML variants use the same final menu, data and shader. Each passed
selection/filtering, keyboard opening/Escape/focus restoration, reduced motion,
and a close/reopen interruption. Captures at fixed 25%, 55% and 100% progress make
the visual comparison independent of screenshot readback delays.

| Variant | Observation | Decision |
| --- | --- | --- |
| Materialize | Full menu appears below a disappearing button; weak spatial connection. | Reject for this nearby trigger. |
| Downward unfold | Width jumps to menu width before height develops; looks like a separate panel. | Reject. |
| Button-to-menu morph | Width, height and curvature grow from the trigger; the top edge stays fixed and the surface expands downward. | Keep. |

The chosen surface opens in 220ms and closes in 160ms without overshoot. Labels
fade in at their final size, so text and hit targets are never stretched. Keyboard
operation and reduced motion skip the transition. As the surface grows, its
existing blur samples spread farther and its tint increases to protect menu
legibility over text. This adds no blur pass or texture to the menu itself.

The popup starts at the button's own top edge. Neither the optical surface nor
the option list translates down during opening, so replacing the button leaves
no empty slot above the menu. `qml_menu_anchor.py` checks that edge at four
progress values, with the header expanded/collapsed and enlarged text.

## Rendering and scrolling

Following the user's source correction, top controls reuse the actual handle
material from `GlassSlider.qml`, extracted into `SelectorLens.qml`. The slider
uses that same component: 6% tint, zero blur, strength 24, flat inner surface,
rim .26 and ring -.8. Selected filters retain their accent outline. The dock's
existing material remains intact. One bounded scene capture serves all top controls; the controls
live outside that capture, preventing recursive feedback. Performance mode
reduces this capture's resolution, as it already does for the dock.

The type picker reserves the animated menu width in the horizontal filter row.
Neighboring buttons move with its expanding edge and return when it closes;
the menu retains its full width and height. The horizontal filter scroller
continues to provide access to buttons beyond the window edge.

Lists render an additional 220 scaled pixels above their viewport, keeping
content visible beneath floating controls without instantiating the full list.
Clipping at internal task-group joins remains. Pixel checks verify both actual
painting above the viewport and content changing the refracted filter pixels.

Evidence and reproducible scripts: `../tests/qml-evidence/top-glass/`,
`../tests/qml_top_glass.py`, and `../tests/qml_menu_variants.py`.
