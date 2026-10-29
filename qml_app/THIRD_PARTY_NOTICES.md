MIT License

Copyright (c) 2026 Rickky

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


## MacShell code used in revision 4

Upstream: https://github.com/0-ss/MacShell
Examined commit: 1bdb51870b621100fd2709f66c8f8e00ab17b9c4 (25 October 2026).

- shaders/glass.frag substantially reuses liquidglass.frag: rounded-box distance
  field, squircle bezel normal, Snell refraction, magnification, dispersion,
  Gaussian disk sampling, tint/vibrancy, depth shading, directional specular and
  meniscus highlights, corner-light border, grain and premultiplied shadow.
- Glass.qml adapts GlassSlab.qml's padded ShaderEffect wrapper and optical scaling.
- LensBar.qml and SettingsPanel.qml adapt local-track capture and press growth
  from GlassSegmented.qml, GlassSlider.qml and GlassSwitch.qml. Native Qt controls
  retain input, focus and accessibility behavior.
- Main.qml's bounded scene crop follows the rendering structure in MacDock.qml /
  MacBar.qml; only this application's synthetic scene is captured.

Modifications include the existing planner palette, eight instead of 24 Gaussian taps, a mip-based one-sample
Performance branch, a direct three-sample zero-blur branch, app-specific texture
coordinates, visibility gating and native control integration. The MIT license
above applies to the reused portions. No upstream artwork, fonts, icons or compiled
shader binaries are copied. QSB packages are built locally with Qt 6.10.2.

Revision 5 rechecked the same upstream main commit and extends those optical
parameters to ButtonGlass.qml / GlassComboBox.qml and existing native controls.
Button press growth uses the grow-and-settle approach in GlassSegmented.qml.
Dock growth is tied to dragging with a shorter release and no post-release hold.
No additional upstream assets, fonts, icons or binaries were copied.
