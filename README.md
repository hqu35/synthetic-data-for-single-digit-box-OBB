# Blender mechanical digit-register data

> **Latest review: [five moderate-perspective views with OBBs](docs/perspective_review.md).**
> The previous 200-view batch was rejected for insufficient visible perspective.
> The current worker defaults to [`configs/perspective_review.json`](configs/perspective_review.json).
> The [industrial-font candidates](docs/industrial_fonts_review.md),
> [corrected band OBBs](docs/obb_band_stage1.md), glass and required mechanical
> references are preserved. Further generation is paused until the user restarts it; the rejected
> 22-image environmental-framing run was removed with explicit cleanup approval.
> See the [cleanup report](docs/cleanup_report.md). Dataset commands below also
> describe legacy functionality and do not authorize a new batch.

A headless Phase II generator with cylindrical UV-printed digit wheels, independently
rotating assemblies, beveled rims and right-side pins, solid viewing apertures,
procedural cream plastic, and geometry-derived `digit_slot` OBBs. All training
samples target nonzero image-space rotation. Real/synthetic dataset mixing is
outside the renderer.

## Run

Validated with Blender **5.1.1**, Cycles **CPU**, Python 3.9, Pillow 11.3 and NumPy
1.26.4. Other Blender versions and Linux have not been runtime-tested. No specific
GPU is required. Install Blender separately, then:

```bash
python3 -m pip install -r requirements.txt
python3 run.py --config configs/preview.json --output outputs/my_batch
```

The wrapper builds/caches the ink atlas, launches Blender and independently audits
the exported files. It finds Blender on PATH or uses the standard macOS application
path; override with `--blender /path/to/blender`. Output must be new or empty.

Native execution (default atlas/font are included):

```bash
python3 prepare_assets.py --config configs/preview.json
blender --background --factory-startup --python-exit-code 1 \
  --python generate.py -- --config configs/preview.json --output outputs/my_batch
python3 validate.py outputs/my_batch
```

On macOS replace `blender` with `"/Applications/Blender.app/Contents/MacOS/Blender"`.
A restricted macOS sandbox may prevent Metal initialization even for CPU rendering;
use a normal terminal. Blender uses its bundled NumPy; Pillow is host-only.

```bash
# Six controlled states, changing only the middle wheel
python3 run.py --rolling-preview --output outputs/my_rolling

# Higher quality: 1024 x 512, 96 samples/pixel versus preview 640 x 320, 16 samples
python3 run.py --config configs/final.json --output outputs/my_final

# Exposed assembly, packed .blend, material/camera comparisons, all-ten-digit UV check
blender --background --factory-startup --python-exit-code 1 \
  --python render_diagnostics.py -- --output outputs/my_diagnostics
python3 review_diagnostics.py outputs/my_diagnostics

# Replay an accepted sample, including its original regeneration attempt and noise
blender --background --factory-startup --python-exit-code 1 \
  --python generate.py -- --replay outputs/upgrade50/metadata/000024.json \
  --output outputs/my_replay
python3 validate.py outputs/my_replay

# Recreate an index using the original configuration/sampling context
python3 run.py --index 24 --output outputs/my_index24
python3 -m unittest discover -s tests -v
blender --background --factory-startup --python-exit-code 1 \
  --python tests/blender_checks.py
```

## Configuration and mechanical layout

`configs/preview.json` is complete; `configs/final.json` inherits it using `extends`.
Inheritance resolves relative to the config file. Configured relative output paths
resolve against the repository; `--output` resolves against the caller's directory.
`--count` changes batch size. Preserve count when reproducing stratified angles;
use `--index` or metadata replay instead.

| Group | Controls |
| --- | --- |
| Batch | `count`, `seed`, `output`, `resolution`, five/six `digit_counts` weights |
| Rotation | Absolute min/max (2–20°), uniform/stratified magnitudes, angle tolerance, spread |
| Geometry | Wheel radius/axial width, bevel, radial segments, rim width/radius, axle radius, clearance |
| Visible slots | Shared gap ratio (0.03–0.20), optional slot width override, aperture height/standoff, frame thickness/border |
| Pins | Enable, 2/3 per numeral interval, radius/length ratios, radial location, bevel |
| Typography | Font path, atlas resolution, numeral height/width fractions |
| Wheels | Transition probability, `transition_progress_min/max` (0.15–0.85) |
| Plastic | Preset, cream color/tint, roughness ramp, aging, color variation, micro bump |
| Ink | Darkness and roughness, driven by the cylindrical texture mask |
| Lights | Broad area size, position, energy, ambient strength, approximate correlated color temperature |
| Camera | Ortho/perspective weights, distance, modest yaw/pitch, framing margin, initial FOV |
| Camera appearance | Neutral/cool/warm/randomized, weights/intensity, white balance, exposure, contrast, blur, noise, optional defocus |
| Randomization | Independent geometry, wheel-state, material, lighting, pose, camera-appearance streams; fixed seed when disabled |
| Rendering | Cycles CPU samples, denoising, threads; bounded generation attempts |

Dimensions use consistent Blender units; defaults are dimensionless engineering
assumptions, not measured real-meter dimensions. For each register:

```text
assembly_width = wheel_width + rim_width + pin_length
pitch = assembly_width + wheel_axial_clearance
slot_width = pitch / (1 + gap_ratio)
visible_gap = slot_width * gap_ratio
pitch = slot_width + visible_gap
center_x[i] = (i - (N - 1)/2) * pitch
```

`slot_width: null` derives the aperture width from the mechanical envelope. A
non-null interval overrides it, and determines pitch through `w + g`; impossible
overlap or coverage is rejected. Physical width, visible slot width and glyph
width are separate. Pin length ratios are relative to body axial width; pin radius
ratios and radial position are relative to wheel radius. The right-side rim and
pins are included in clearance exactly once. Tight gaps limit feasible protrusion
lengths. Increasing pin length requires compatible gap/width/clearance settings.

All body/rim/pin assemblies have independent +X axle rotations. Ten numeral
intervals give 20 or 30 uniformly spaced pins per wheel. Pins share their wheel's
parent and do not act as the stationary separators. Most are hidden in training
views, which is intentional. Frame, surround and separators are solid meshes;
the frame reveals the front arc of each cylinder. No flat cards or text meshes
are used for printed numerals.

## Cylindrical print and rolling calibration

The included OFL **Barlow Condensed SemiBold** font is rasterized into ten horizontal
circumferential segments in a 2560 x 512 grayscale ink mask. Font/atlas checksums
are recorded and verified before scene construction. Custom fonts/resolution/scale
can be configured; regenerate assets before native Blender execution.

The body mesh uses `(x, R sin(a), R cos(a))` with UV coordinates:

```text
u = a / (2*pi) + 0.05   # periodic circumference; digit d centered at (d + 0.5)/10
v = x / wheel_width + 0.5
wheel_rotation = (digit + transition_progress) * 2*pi/10  # radians about +X
phi0 = 0, sign = +1, 0 <= transition_progress < 1
```

Atlas raster orientation accounts for PNG Y-down, cylinder angle-up and axial
X-right. All ten stable digits have rendered calibration examples and an automated
surface/atlas lookup test against the upright font. The seam lies between printed
cells, with zero ink at both texture edges. Actual cylinder rotation moves the
current numeral down and its successor in from above; 9→0 is periodic and continuous.
There is no alpha blend, carry propagation or numerical synchronization.

## Plastic and ink

`digitgen/materials.py` reproduces the supplied guide's structure:

```text
Generated -> Mapping -> Noise A -> ColorRamp A -> Base Color
                       Noise A -> ColorRamp B -> Roughness
                       Noise B Fac --\
                                      Math MULTIPLY -> inverted Bump -> Normal
                       Noise C Fac --/
```

All three Noise Vector inputs come from the same Mapping node. Noise A is 3D fBM,
scale 100/detail 10/roughness 1/distortion 0.1; B is fBM, 20/8/0.9/0.1; C is
Multifractal, 30/10/1/2. Lacunarity is 2. Roughness ramp positions are 0.3 and 0.8,
not output roughness values. Metallic is 0 and IOR is 1.5.

`reference_dark_plastic` uses inverted Bump Strength **0.05**, Distance **1.0**, and
a black-to-white roughness ramp, with a near-black color ramp. Exact final color
endpoint values are uncertain in the guide; these are a documented approximation.
`meter_cream_matte` keeps the graph, uses a warm cream ramp and roughness outputs
0.55–0.80, and reduces bump to strength 0.01–0.025 and distance 0.004 at this wheel
scale. This prevents a rocky or damaged-surface appearance. `basic` is provided
for the diagnostic comparison. The ink mask mixes substrate/ink color and roughness
on the actual wheel surface; ink has no geometric relief. Rims, pins, axle and frame
use distinct suitable materials. Reference-dark comparison uses pale printed ink
for legibility; cream/basic use dark ink.

The guide was read at
`/Users/ququ/Documents/Codex/2026-10-28/chat-354-midterm-ii-access-to-2/outputs/Plastic_Shader_Guide/Plastic_Shader_操作指南.md`.
See [shader implementation notes](docs/shader.md) for values and provenance.

## Separate photographic controls

Material color, lighting color, camera white balance, camera exposure and postprocess
color cast are separately stored. Cream plastic remains cream in cool photographs.
Area-light temperature uses an explicitly approximate RGB mapping, not a measured
spectral light model. Ordinary training illumination uses broad, modest lights;
extra grazing lighting exists only in the exposed diagnostic.

Raw RGB is saved through Blender's AgX view transform as sRGB. Inside Blender's
Python process, `camera_appearance.py` decodes this display-referred sRGB to linear
RGB, applies white-balance and cast channel gains, exposure in stops, contrast about
0.18, Gaussian softness and seeded Gaussian sensor noise, then clips and re-encodes
sRGB. This is a simplified photographic model, not RAW sensor simulation or a
scene-linear pre-AgX transform. Clipped-channel fraction is measured; >3% rejects
an attempt. Optional physical defocus uses Blender camera DOF; it is disabled by
default. There is no distortion, crop, resize or pixel-coordinate transform.

## Annotation contract

One class: `0 = digit_slot`. Labels represent each wheel's **visible stationary
aperture**, excluding side mechanics and the inner frame wall. The visible region
is the intersection of projected front and back aperture openings of the solid
frame. This convex polygon may have more than four vertices. Its minimum-area
enclosing rectangle is fitted in **pixel space**, then normalized:

```text
0 x1 y1 x2 y2 x3 y3 x4 y4
```

Pixels use +X right, +Y down; Blender's projected Y is inverted on export. Corners
are clockwise local TL/TR/BR/BL along the near-horizontal width axis, which need
not start at the globally topmost point. OBB angles are measured clockwise from
image +X, independently of wheel axle radians. Camera-roll sign is calibrated on
the projected width direction, and actual per-slot OBB angles are checked against
targets. Default target error <=0.8°, within-register spread <=1°.

The cylinder's full curved silhouette is not the target. Four aperture-plane corners
are sufficient for each opening; the frame-depth intersection handles its geometric
occlusion. Nine near-boundary/interior rays at the back opening verify coverage by
the intended wheel. Invalid narrow-gap/perspective combinations are explicitly
rejected and regenerated. This conditions the accepted parameter distribution;
inspect its saved gap/angle statistics. Coordinates are never silently clamped.

Each rolling wheel still has one slot box. Boxes remain stable with a fixed camera
and aperture. Overlays reread the exact exported label text. Compatibility with
real or pretrained **tight-glyph OBBs remains unverified**; those targets are not
interchangeable with this slot convention.

## Outputs, validation and provenance

```text
outputs/upgrade50/
  images/000000.png             # Final photographic RGB
  raw_images/000000.png         # AgX RGB before camera appearance
  labels/000000.txt
  metadata/000000.json          # Config, sampled parameters, assets, matrices, graph
  overlays/000000.svg           # Embedded final RGB + exact saved labels
  overlays/000000.png           # Independent host auditor
  config.resolved.json
  classes.json
  manifest.json                # Successful records and rejected attempts
  validation/summary.json
  validation/failures.json
  validation/contact_sheet.png
```

Sampling uses independent seeded streams; disabled randomization groups use a
fixed group seed. Geometry can therefore remain fixed while light/material/camera
appearance changes. Metadata schema **2** stores physical states, pin density and
envelope, texture/font checksums, shader graph, light/camera parameters, requested
and measured OBB angles, visible aperture polygons, processing settings and source
hash. Schema-1 curved-mesh baseline data remains in its original output folders;
it is not replayed by the upgraded renderer. Cross-build/platform pixel identity
is not guaranteed. No automatic train/validation split or real-image sampler is
created for this technical batch.

The auditor decodes every PNG and checks physical envelopes, pin counts, states,
raw/final dimensions, asset hashes, label count/order, finite coordinates, bounds,
rectangle geometry, enclosure, angles, metadata agreement and aperture contrast.
Tests additionally check actual Blender UVs, shader topology/settings, pin attachment,
rolling wraparound and 250 wheel-state OBB-invariance cases. Material and camera
comparison scene invariance is audited separately. Visual inspection remains
necessary: geometry checks do not establish photorealism or detector performance.
See [the current validation report](docs/upgrade_validation.md).

The [previous Three.js pipeline](https://github.com/hqu35/water-meter-synthetic-data-pipeline)
was inspected read-only for layout, projection and appearance conventions. This
project preserves its own tested projection/export pipeline and depends on no old
runtime or assets. No diffusion, training, Phase I/III, carry mechanics, full meter
housing or cluster infrastructure is included.

Font provenance: [Google Fonts Barlow Condensed](https://github.com/google/fonts/tree/main/ofl/barlowcondensed),
with [the included OFL license](assets/fonts/OFL.txt). The procedural renderer has no
external textures or HDRIs. The four requested mechanical/real-register photographs
were not found among available files; the later supplied images are shader-tutorial
screenshots. Matching to those four mechanical photographs remains unverified.

## Independent font and glass review

Industrial font presets: [review report](docs/industrial_fonts_review.md).
Native physical protective cover: [glass report](docs/glass_review.md).
These fixed review artifacts preserve the approved mechanics and defer atlas spacing/transition calibration.
Formal dated deliveries are indexed in [DELIVERIES.md](DELIVERIES.md); source `outputs/` folders are staging.

## Numeral-band annotation correction — Stage 1 checkpoint

[Single-sample report and review artifacts](docs/obb_band_stage1.md). The approved
raised-register model now has a mesh-derived `visible_numeral_band` adapter in
`digitgen/band_annotations.py` and a fixed review entry point `obb_band_stage1.py`.
Its class 0 covers the central printed cream band rather than the whole slot;
the legacy baseline generator above retains its historical aperture semantics.
Exactly one reference RGB was rendered. Stage 2's 100-pair dataset requires human
approval of this corrected overlay and has not started.
