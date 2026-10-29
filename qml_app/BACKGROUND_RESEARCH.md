# Background references — updated 29 October 2026

The production refresh uses original analytic shader artwork inspired by the
user's macOS references: Satin's indigo/pearl sheets, Tide's blue glass crests and
Dunes' warm pearl/mauve folds. They replace Contour, Flow and Horizon at the same
preference indices. Soft colours is unchanged, verified pixel-for-pixel at a fixed
phase in all four themes. No generated or downloaded image assets are bundled.
Antialiased edges, broad reflected light and subtle static dither keep the curves
smooth. Light/dark variants share the existing bounded layer and animation gates.
Offscreen D3D11 captures cover all backgrounds, all themes, both rendering modes
and compact/wide windows in `tests/wallpaper-refresh/`.

The notes below record the earlier prototype research.

Research used Scrapling `make_request` and `bulk_get` on Apple's own pages.
The support page's `main` selector was empty; retrieving `body` recovered the
actual wallpaper instructions. Newsroom `picture` and `.image-description`
selectors returned image URLs, alt text and captions. No wallpaper assets were
copied into the prototype, and no additional runtime dependencies were introduced.

## References and design choices

- [Apple: Customize the wallpaper on your Mac](https://support.apple.com/en-euro/guide/mac-help/mchlp3013/mac):
  describes dynamic wallpapers, light/dark still variants, landscapes, creative
  pictures and colours. The prototype adopts a small choice of original backgrounds
  with automatic palette adaptation, rather than implementing a wallpaper library.
- [Apple: macOS Big Sur](https://www.apple.com/newsroom/2020/06/apple-introduces-macos-big-sur-with-a-beautiful-new-design/):
  official desktop/Dock/Control Center reference imagery and design context.
- [Apple: macOS Monterey](https://www.apple.com/newsroom/2021/06/macos-monterey-introduces-powerful-features-to-get-more-done/):
  official desktop imagery as a reference for the abstract wallpaper direction.

The earlier Flow's sweeping bands and Horizon's layered landscape were our interpretation of
that direction, not reproductions of particular Apple wallpapers. Contour retains
the prototype's quiet folded surface. Soft colours directly follows the five
blurred fields in `planner_html.py`: blue upper left, purple upper right, teal
below, plus warm and pink fields. Clear substitutes the existing cooler palette;
Vivid retains the more colourful palette. Light mixes toward the light base;
Dark lowers the colour fields' luminance. Auto follows the operating system.

Every option uses the existing single layered wallpaper, at most 1200×800, with
mipmaps. Only the selected branch executes. No desktop windows, external textures,
Python frame callbacks, new offscreen layers or extra blur passes are introduced.
Animation uses the existing QML phase, joins at 2π, and stops under existing
Performance/reduced-motion/inactive-window rules.

## Qt verification

- [Qt Item layer.smooth](https://doc.qt.io/qt-6/qml-qtquick-item.html#layer.smooth-prop):
  smooth sampling is explicitly enabled on the shared wallpaper layer.
- [Qt ShaderEffectSource](https://doc.qt.io/qt-6/qml-qtquick-shadereffectsource.html):
  the existing dock/track textures use mipmaps and smooth sampling too.
- [Qt Slider](https://doc.qt.io/qt-6/qml-qtquick-controls-slider.html#snapMode-prop):
  `NoSnap`, `stepSize: 0` and a real-valued setting provide continuous pointer
  input. Native arrow-key control is retained. Refraction is not bound to frosting;
  a separate Distortion slider independently controls the optical multiplier.

The glass finish raises the minimum sampled mip level from 0 to 4 and gradually
adds a neutral translucent coating. It leaves the refracted texture coordinates,
optical thickness, dispersion and magnification unchanged. Native D3D11 pixel
checks, theme screenshots and measured limitations are in
the historical prototype captures, removed during the v3 cleanup.

## Wheel input

[Qt WheelHandler](https://doc.qt.io/qt-6/qml-qtquick-wheelhandler.html) handles
mouse and touchpad input. [Qt WheelEvent](https://doc.qt.io/qt-6/qml-qtquick-wheelevent.html)
distinguishes angle deltas from high-resolution pixel deltas. The implementation
uses an interruptible 180 ms QML animation for wheel notches and directly applies
pixel deltas. It respects the delivered direction, without inverting the user's
system preference a second time. Reduced motion applies either input directly.
Native dragging and scrollbars are retained. No Python frame callback is added.
