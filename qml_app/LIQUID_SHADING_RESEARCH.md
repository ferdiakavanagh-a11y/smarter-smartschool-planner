# Liquid Glass shading and corners — 2026-10-27

Read with Scrapling: HTTP fetch of the two WWDC transcripts, then browser fetch
of the JavaScript-rendered Materials guideline. These sources describe Apple's
design; they do not publish its renderer or numerical shader parameters.

## Source observations

- [Meet Liquid Glass, WWDC25](https://developer.apple.com/videos/play/wwdc2025/219/):
  lensing defines transparent forms. Highlights follow geometry. Shadows adapt
  to underlying detail, larger surfaces have greater depth, and surrounding
  colour can scatter into the shadow (6:00–8:29 and 10:44–11:58).
- [Get to know the new design system](https://developer.apple.com/videos/play/wwdc2025/356/):
  rounded shapes, capsules and concentric radii create a coherent layout;
  pinched corners and extra borders undermine it.
- [Materials guideline](https://developer.apple.com/design/human-interface-guidelines/materials):
  reserve Liquid Glass primarily for floating controls/navigation; use quieter
  materials for content. Maintain legibility and accessibility alternatives.

## Implementation choices

The prototype keeps the user's requested transparent content groups and layout.
Its material is an approximation of those optical principles, not Apple's
proprietary implementation or a claim of pixel-identical native rendering.

- The shared shader uses a fourth-order corner curve with its matching normal
  for panel geometry, lensing, highlights and shadow. Capsules stay circular.
- Replace the near-white perimeter stroke with directional edge reflections.
- Compare two existing backdrop mip levels only on exterior shadow pixels to
  approximate local detail; modulate density and carry ambient colour into the
  premultiplied shadow. This is a contrast heuristic, not text recognition.
- Broader panels have a longer penumbra with 16px padding; small controls keep
  10px. No new render targets, blur passes or per-frame Python work.
- Give list clipping enough horizontal room for the penumbra. Clip virtualized
  task slices only at internal joins, preserving rounded group ends and shadows.
- Keep independent frosting/distortion, continuous dock geometry and the opaque
  high-contrast fallback. The fallback deliberately uses native rounded rectangles.

Surface content still samples the controlled wallpaper; the dock samples the
application scene. This does not add OS-wide scene capture or native Apple APIs.
Historical prototype captures were removed during the v3 cleanup; see handoff.md for current verification.
