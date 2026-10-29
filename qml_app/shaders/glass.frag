#version 440
// Adapted from MacShell liquidglass.frag at 1bdb51870b621100fd2709f66c8f8e00ab17b9c4.
// Copyright (c) 2026 Rickky. MIT; see ../THIRD_PARTY_NOTICES.md.
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 itemSize;      // whole shader item in px (glass + pad on every side)
    vec2 glassSize;     // the Dock rectangle in px
    vec2 srcSize;       // backdrop texture size in px
    vec2 srcOffset;     // where the item's top-left sits inside the backdrop texture, px
    float pad;          // item padding around the glass (room for the drop shadow)
    float radius;       // corner radius, px
    float bezel;        // width of the refracting rim, px
    float thickness;    // how far the rim shifts the backdrop, px
    float dispersion;   // chromatic split (0 = none)
    float blurPx;       // backdrop blur radius, px
    float tintMix;      // 0..1 amount of flat tint (the "translucency" slider)
    float saturation;   // backdrop saturation boost
    float dark;         // 0 = light mode, 1 = dark mode
    float debug;        // 1 = show the raw backdrop texture (magenta = texture is empty)
    float rim;          // specular edge highlight strength (1 = original strength)
    float grain;        // fine noise amplitude over the whole glass
    float magnify;      // vertical lens magnification of the whole slab
    float shadowAmt;    // drop-shadow strength (1 = original, 0 = none) - appended last so older layouts stay compatible
    float rimTint;      // 0 = white rim (Dock / Menu Bar), 1 = rim + border take a brighter shade of the glass's own colour (widgets)
    float ringW;        // width in px of a thin border line along the very edge (0 = none)
    vec4 surfaceColor;
    float quality;
    float flatInner;    // 1 = no inner edge shading (the darker inner rim); 0 = original. Appended last, unset = 0
    float sheen;        // Disabled on virtualized slices so one group has no per-row lighting seams.
    float frost;
};

layout(binding = 1) uniform sampler2D src;

// Eight mip-filtered taps retain the upstream Gaussian optics on these small surfaces.
const int   TAPS   = 8;
const float GOLDEN = 2.39996323;

// Natural blur, no "duplicated background" ghosts:
//  * every tap reads a pre-blurred mip level sized to the gap between taps, so the taps overlap into one
//    smooth surface instead of showing as separate copies of the content
//  * Gaussian weights give a soft falloff instead of a hard disk edge
//  * the tap pattern is rotated per pixel (interleaved gradient noise), so any leftover gaps turn into
//    fine grain instead of repeating ghost lines
//  * one shared pattern for all three colour channels (dispersion only shifts the centre)
// Needs `mipmap: true` on the ShaderEffectSource (set in MacBar.qml / MacDock.qml).
vec3 backdropLod(vec2 pItem, float lod)
{
    vec2 uv = (pItem + srcOffset) / srcSize;
    // Reuse the shared mip chain: frosting adds no textures or sampling passes.
    vec4 sampleColor = textureLod(src, clamp(uv, vec2(0.001), vec2(0.999)), max(lod, frost*4.0));
    return sampleColor.rgb + surfaceColor.rgb * (1.0 - sampleColor.a);
}

float ign(vec2 p)
{
    return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715))));
}

vec3 blurredDisp(vec2 pItem, vec2 disp, float disperse, float rad)
{
    if (quality < 0.5) {
        return backdropLod(pItem + disp, clamp(log2(max(rad, 1.0)), 0.0, 5.0));
    }
    if (rad < 0.1) {
        // Flat interiors have identical channel coordinates; one fetch is exactly equivalent.
        if (dot(disp, disp) == 0.0) return backdropLod(pItem, 0.0);
        return vec3(backdropLod(pItem + disp * (1.0 + disperse), 0.0).r,
                    backdropLod(pItem + disp, 0.0).g,
                    backdropLod(pItem + disp * (1.0 - disperse), 0.0).b);
    }
    float R   = max(rad, 0.5) * 1.5;                       // Gaussian reaches further than a flat disk
    float gap = R * sqrt(3.14159265 / float(TAPS));        // spacing between neighbouring taps, px
    float lod = clamp(log2(max(gap, 1.0)) + 0.35, 0.0, 6.0);
    float rot = ign(gl_FragCoord.xy) * 6.2831853;
    vec3  acc = vec3(0.0);
    float wsum = 0.0;
    for (int i = 0; i < TAPS; ++i) {
        float fi = float(i) + 0.5;
        float r  = sqrt(fi / float(TAPS));
        float a  = fi * GOLDEN + rot;
        float w  = exp(-2.2 * r * r);
        vec2  o  = vec2(cos(a), sin(a)) * r * R;
        vec3  c;
        c.r = backdropLod(pItem + o + disp * (1.0 + disperse), lod).r;
        c.g = backdropLod(pItem + o + disp,                    lod).g;
        c.b = backdropLod(pItem + o + disp * (1.0 - disperse), lod).b;
        acc  += c * w;
        wsum += w;
    }
    return acc / wsum;
}

float hash12(vec2 p)
{
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

// Continuous-curvature corners for panels; capsules retain their circular ends.
float glassDistance(vec2 q, vec2 hs, float r, out vec2 normal)
{
    bool capsule = r >= min(hs.x, hs.y) * 0.99;
    if (!capsule) r = min(r * 1.6, min(hs.x, hs.y));
    vec2 d = abs(q) - (hs - r);
    vec2 v = max(d, 0.0);
    vec2 signs = mix(vec2(-1.0), vec2(1.0), step(vec2(0.0), q));
    if (max(v.x, v.y) < 0.001) {
        normal = d.x > d.y ? vec2(signs.x, 0.0) : vec2(0.0, signs.y);
        return max(d.x, d.y) - r;
    }
    if (capsule) {
        normal = normalize(v) * signs;
        return length(v) - r;
    }
    vec2 v2 = v * v;
    float norm = sqrt(sqrt(dot(v2, v2)));
    vec2 gradient = v2 * v / max(norm * norm * norm, 0.001);
    float gradientLength = max(length(gradient), 0.001);
    normal = gradient / gradientLength * signs;
    return (norm - r) / gradientLength;
}

void main()
{
    vec2 p  = qt_TexCoord0 * itemSize;
    vec2 hs = glassSize * 0.5;
    vec2 q  = p - vec2(pad) - hs;
    float r = min(radius, min(hs.x, hs.y));

    vec2 g;
    float sd = glassDistance(q, hs, r, g);
    float aa = max(fwidth(sd), 0.001);
    float cov = smoothstep(-aa * 0.5, aa * 0.5, -sd);

    if (debug > 0.5) {
        vec4 s = texture(src, clamp((p + srcOffset) / srcSize, vec2(0.001), vec2(0.999)));
        fragColor = (s.a < 0.01 ? vec4(1.0, 0.0, 1.0, 1.0) : vec4(s.rgb / max(s.a, 1e-3), 1.0)) * cov * qt_Opacity;
        return;
    }

    // Only the exterior samples ambient light/detail; reuse the backdrop mip chain.
    vec4 shadow = vec4(0.0);
    if (cov < 1.0 && shadowAmt > 0.0) {
        float elevation = smoothstep(40.0, 160.0, min(glassSize.x, glassSize.y));
        float offset = mix(1.5, 3.0, elevation);
        vec2 shadowNormal;
        float sds = glassDistance(q - vec2(0.0, offset), hs, r, shadowNormal);
        float tail = 1.0 - smoothstep(-3.0, pad - offset, sds);
        vec3 ambient = backdropLod(p, 3.0);
        vec3 local = backdropLod(p, 0.0);
        float detail = clamp(length(local - ambient) * 2.0, 0.0, 1.0);
        float luminance = dot(ambient, vec3(0.2126, 0.7152, 0.0722));
        float density = mix(0.14, 0.23, elevation) + 0.16 * detail;
        float alpha = density * mix(1.15, 0.75, luminance) * shadowAmt * tail * tail;
        // Reflected ambient colour keeps the penumbra from becoming a black outline.
        shadow = vec4(ambient * 0.45 * alpha, alpha);
    }
    if (cov <= 0.0) {
        fragColor = shadow * qt_Opacity;
        return;
    }

    // ── distance to edge + outward edge direction ──
    float t = max(-sd, 0.0);

    // ── convex squircle bezel → surface normal ──
    float bz   = max(bezel, 1.0) * 1.45;           // wider bezel: the glass reads thicker
    float u    = clamp(t / bz, 0.0, 1.0);
    float om   = 1.0 - u;
    float om4  = om * om * om * om;
    float slope = (om * om * om) / pow(max(1.0 - om4, 1e-3), 0.75);
    slope = min(slope, 7.0);
    vec3 n = normalize(vec3(g * slope, 1.0));

    // ── refraction: glass n≈1.5, ray enters straight down ──
    vec3 rd   = refract(vec3(0.0, 0.0, -1.0), n, 1.0 / 1.5);
    vec2 disp = rd.xy / max(-rd.z, 0.2) * thickness * 1.35;

    // the whole slab acts as a gentle vertical lens; blur is crisper right at the curved rim
    vec2 ps = vec2(p.x, (p.y - pad - hs.y) * (1.0 - magnify * 1.5) + pad + hs.y);
    float rad = blurPx * mix(0.45, 1.0, smoothstep(0.0, bz, t));

    vec3 col = blurredDisp(ps, disp, dispersion * 0.6, rad);

    // Clear lenses retain source contrast; diffuse lift is opt-in for the existing dock.
    float l = dot(col, vec3(0.2126, 0.7152, 0.0722));
    col = mix(vec3(l), col, saturation);
    vec3 tintC = surfaceColor.rgb;
    col = mix(col, tintC, tintMix);
    col = mix(col, mix(vec3(1.0), vec3(.80,.85,.89), dark), frost*mix(.48,.25,dark));
    col += mix(0.055, 0.020, dark) * sheen;

    // ── depth: soft top sheen, darker lower inner edge ──
    float ty = clamp((q.y + hs.y) / glassSize.y, 0.0, 1.0);
    col += (1.0 - ty) * mix(0.040, 0.030, dark) * sheen;
    float innerK = 1.0 - clamp(flatInner, 0.0, 1.0);
    col *= 1.0 - 0.12 * exp(-t / 6.0) * clamp(g.y, 0.0, 1.0) * innerK;
    col *= 1.0 - 0.10 * exp(-t / (bz * 0.45)) * innerK;          // thick glass absorbs light toward the edge (heavier feel)

    // colour of the rim / border: white, or (rimTint) a brighter shade of what the glass looks like at this spot
    vec3 rimCol = mix(vec3(0.96, 0.98, 1.0), clamp(col * 1.5 + 0.12, 0.0, 1.0), rimTint);

    // ── specular rim, light from the top-left ──
    vec2  L      = normalize(vec2(-0.55, -0.83));
    float facing = dot(g, L);
    float spec   = pow(max(facing, 0.0), 1.6) + 0.55 * pow(max(-facing, 0.0), 2.2);
    float hair   = exp(-t / 1.1);
    float wide   = exp(-t / 5.0);
    float edgeHi = hair * (0.18 + 0.78 * spec) + wide * 0.10 * (0.30 + spec);
    edgeHi *= rim * mix(0.85, 1.0, dark);
    col += edgeHi * rimCol;

    // meniscus: a soft second highlight inside the rim, like surface tension pulling the liquid together
    float mx  = (t - bz * 0.5) / (bz * 0.2 + 1.0);
    float men = exp(-mx * mx);
    col += men * 0.07 * (0.35 + spec) * rim * rimCol;

    // thin border line right at the edge (anti-aliased), brighter on the lit side
    if (ringW > 0.0) {
        float ring = 1.0 - smoothstep(ringW * 0.5, ringW * 0.5 + 1.0, t);
        col = mix(col, rimCol, ring * (0.55 + 0.35 * clamp(facing * 0.5 + 0.5, 0.0, 1.0)));
    }

    // A light-catching edge follows the surface normal instead of tracing a white border.
    if (ringW < 0.0) {
        float rw   = -ringW;
        float ring = 1.0 - smoothstep(rw * 0.5, rw * 0.5 + 1.0, t);
        col = mix(col, rimCol, ring * (0.08 + 0.38 * spec));
    }

    // fine triangular-distribution grain, same on every channel so it reads as texture, not colour noise
    float gn = hash12(gl_FragCoord.xy) + hash12(gl_FragCoord.xy * 1.7 + 17.0) - 1.0;
    col += gn * grain;

    col = clamp(col, 0.0, 1.0);

    fragColor = (vec4(col, 1.0) * cov + shadow * (1.0 - cov)) * qt_Opacity;
}
