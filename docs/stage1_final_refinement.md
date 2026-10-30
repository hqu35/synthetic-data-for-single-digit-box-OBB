# Stage 1 — final geometry and numeral-surface refinement

**Status: fixed inspection package delivered; STOP for human approval.**
No glass, randomized training images, diffusion or model training was added.
The existing cylindrical base, annular raised band, real shoulders, axle parenting
and slot-OBB projection/export helpers are retained.

## Geometry and pin calibration

| Control | Actual value |
| --- | ---: |
| Slot width (unchanged) | 0.640625 |
| Center pitch (unchanged) | 0.717500 |
| Base radius / band radius (unchanged) | 1.10 / 1.25 |
| Raised step (unchanged) | 0.15 |
| Base width (unchanged) | 0.620000 |
| New band width | 0.4484375 |
| `band_to_slot_ratio` | 0.70 |
| Band center | Exactly 0.0 in local axial X |
| Left / right lateral region | 0.09609375 / 0.09609375 |
| Edge-collar width | 0.015 |
| Pin radius / length | 0.027 / 0.060 |
| Pin root / center / tip X | 0.23921875 / 0.26921875 / 0.29921875 |
| Pin radial center | 1.225 |
| Free axial clearance | 0.0975 |
| Digit gap ratio / visible gap (unchanged) | 0.12 / 0.076875 |

Only the band was narrowed and centered; the slot, pitch and drum diameters were
not scaled or cropped to obtain the ratio. Pins were slightly shortened to keep
all silhouettes clear of the frame in the peripheral perspective slots. The same
clearance as the preceding model is retained.

The calibration searches uniform full-wheel pitches and phases, accounting for
aperture height, pin radius, safety margins and all five fixed wheel states.
Candidate pins must not create extra partly visible boundary protrusions in the
reference view. Camera projection, silhouette containment and occlusion rays then
verify the chosen physical meshes. The full count is therefore derived from the
visible target rather than treated as proof of visibility.

| Target | Full-wheel pins | Angular pitch | Phase offset | Render result |
| --- | ---: | ---: | ---: | --- |
| 3 | 30 | 12° | 0° | Three complete, separated pins in each of the five reference slots |
| 4 | 40 | 9° | 4.5° | Four complete pins in the matched single-slot render |

The four-pin configuration was additionally projected and ray-tested on all five
slots in the saved scene: `[4, 4, 4, 4, 4]`. This additional check generated no new
images. Physical pin size, base/band construction, camera, lights and material
remain identical between the three- and four-pin close-ups.

For the full-register camera, bisection of actual projected front/back opening
containment gives approximately **−17.738° to +17.660°** for rim centers. Accounting
for the complete physical pin silhouette narrows the usable interval to about
**−16.404° to +16.333°**. These are global front-arc angles; wheel rotation shifts
which local pin indices occupy them. All reference-view pins lie inside this
interval, with positive projected separation.

### Per-wheel measured reference visibility

Coordinates are pixels in the 1600 × 540 final full-register PNG. Counts refer to
the front arc; complete records also distinguish back pins whose centers project
into the opening but are occluded by physical geometry.

| Wheel | Total | Geometric front count | Actually visible | Projected centers (x, y) | Adjacent center spacing (px) |
| --- | ---: | ---: | ---: | --- | --- |
| 0 | 30 | 3 | 3 | (351.59, 171.81); (350.79, 269.89); (351.70, 367.80) | 98.09, 97.91 |
| 1 | 30 | 3 | 3 | (627.61, 171.79); (627.25, 269.91); (627.66, 367.86) | 98.13, 97.95 |
| 2 | 30 | 3 | 3 | (903.88, 171.76); (903.94, 269.93); (903.85, 367.92) | 98.17, 97.99 |
| 3 | 30 | 3 | 3 | (1180.38, 171.74); (1180.88, 269.95); (1180.28, 367.99) | 98.22, 98.03 |
| 4 | 30 | 3 | 3 | (1457.39, 186.26); (1458.02, 284.83); (1456.62, 382.42) | 98.57, 97.60 |

The 1000 × 1000 three-pin close-up has centers approximately
`(759.39, 254.60), (760.29, 500.00), (759.39, 745.40)`, with 245.40-pixel adjacent
spacing. The four-pin variant has centers
`(759.16, 224.71), (760.16, 407.12), (760.16, 592.88), (759.16, 775.29)`, with spacing
182.41, 185.76 and 182.41 pixels. The silhouettes are well separated, not merged
shapes or pins visible only at extreme opening boundaries.

Every inspected state has its positions, spacing, silhouette bounds and ray hits
in [the detailed report](../outputs/stage1_final_refinement/inspection_report.json).
[CSV](../outputs/stage1_final_refinement/pin_visibility.csv) lists all inspected
wheels/states; [all-pairs distances](../outputs/stage1_final_refinement/pin_pairwise_spacing.json)
include nonadjacent pairs as well.

## Typography and rolling

The font is **Barlow Condensed Regular (400)**, replacing SemiBold (600), using the
included OFL font files. The actual loaded font identity and lower stroke coverage
were tested. `glyph_width_scale = 0.82` and `glyph_height_scale = 0.82` independently
scale the previous normalized 0.78-width / 0.77-height glyph layout. Effective
normalized extents are 0.6396 and 0.6314. The comparison holds the new 70% band,
geometry, camera, lighting, charcoal ink color and surface shader fixed.

Font family, weight, file, width/height scales, horizontal/vertical alignment and
ink color are explicit configuration fields. Family/weight are checked against the
font file rather than merely recorded as labels. Defaults are centered. Physical
circumferential numeral pitch remains **36°**, and the periodic atlas seam remains
between 9 and 0. The full ten-digit mask is 10240 × 1024; smaller glyphs do not change
wheel rotation or numeral angular centers.

Stable 4 and 4→5 at 0.25, 0.50 and 0.75 were rendered using actual axle rotation.
At the midpoint, approximately **46.56% of each glyph's vertical span** lies inside
the aperture. That is a geometric span measure, not a claim that each silhouette
has exactly half its ink area visible. Stable glyphs remain completely inside the
opening. The saved .blend was reloaded and the physical slot OBB reprojected at
all four states: the coordinates were exactly unchanged.

A remaining mechanical visibility limit is explicitly recorded: at exact midpoint,
two front pin centers remain inside and two more pins are partially visible at
the aperture edges (four visible pieces total). At 0, 0.25 and 0.75, three pins are
fully inside. The reference `00054` and controlled four-pin variant meet their
complete-pin targets. Pin phase is not artificially changed while rolling to hide
natural entrance/exit behavior.

## Printed ink reflectance

| Property | Plastic | Ink |
| --- | --- | --- |
| Metallic | 0 | 0 |
| Roughness | Procedural 0.65–0.78 | 0.30 |
| IOR | 1.5 | 1.5 |
| Specular IOR level | 0.50 | 0.55 |
| Micro-bump strength | 0.016 | 0.00128 (8% of substrate) |
| Color | Existing cream | Charcoal `[0.018, 0.020, 0.022]` |

The same cylindrical mask interpolates printed color, roughness, specular IOR
level and micro-bump strength on the shared surface. There is no raised ink mesh,
white highlight texture, emission or bloom. `ink_gloss_enabled` disables the smooth
ink response for the uniform-matte comparison; both samples retain the same print
mask and lighting. Blender **5.1.1** supports the `Specular IOR Level` socket; the
saved material and packed texture were independently checked after reload.

The ink comparison uses the same modest additional rectangular reflection light
for both images, making the effect easier to inspect. The main reference views
retain the original directional lights. Visual inspection shows a smoother
specular response on the dark ink while the plastic stays matte. Across 34,497
sampled dark-numeral pixels, the mean signed RGB change was about **4.52/255**;
localized highlights reach **85/255** difference. This difference is from rendering
material reflectance, not compositing. The inspection light intentionally makes
local highlights more evident than the ordinary reference illumination.

## Review images and artifacts

- [A — Three fully visible pins, centered 70% band](../outputs/stage1_final_refinement/A_three_visible_pins.png)
- [B — Four fully visible pins, matched camera](../outputs/stage1_final_refinement/B_four_visible_pins.png)
- [C — Fixed 00054 register](../outputs/stage1_final_refinement/C_fixed_00054_register.png)
- [D — Previous versus revised typography](../outputs/stage1_final_refinement/typography_comparison.png)
- [E — Stable 4 and rolling sequence](../outputs/stage1_final_refinement/rolling_sequence.png)
- [F — Uniform matte versus glossy ink](../outputs/stage1_final_refinement/ink_surface_comparison.png)
- [G — Five saved-label slot OBBs](../outputs/stage1_final_refinement/G_slot_obb_overlay.png)
- [Three/four-pin comparison](../outputs/stage1_final_refinement/pin_comparison.png)
- [All eleven fixed review renders](../outputs/stage1_final_refinement/inspection_contact_sheet.png)
- [Packed Blender scene](../outputs/stage1_final_refinement/final_stage1_review.blend)
- [Saved-scene shader/OBB verification](../outputs/stage1_final_refinement/saved_scene_verification.json)
- [Artifact audit](../outputs/stage1_final_refinement/artifact_audit.json)

The one diagnostic YOLO polygon label file has five physical-slot OBBs. Its overlay
rereads the exact exported coordinates using the established projection and export
helpers. No slot-target redesign, geometric postprocessing or randomized dataset
export was introduced. Zero/near-zero camera roll is appropriate for this fixed
geometry review and is not a training-angle distribution change.

## Reproduce the fixed inspection only

From the repository root, use a new/empty output directory:

```bash
python3 -c 'import json; from prepare_assets import prepare; c=json.load(open("configs/stage1_final_refinement.json")); prepare(c); prepare({"typography":c["previous_typography"]})'
"/Applications/Blender.app/Contents/MacOS/Blender" \
  --background --factory-startup --python-exit-code 1 \
  --python stage1_final_refinement.py -- \
  --config configs/stage1_final_refinement.json \
  --output outputs/stage1_final_refinement
"/Applications/Blender.app/Contents/MacOS/Blender" \
  --background --factory-startup --python-exit-code 1 \
  --python verify_final_stage1_scene.py -- --output outputs/stage1_final_refinement
python3 review_final_stage1.py outputs/stage1_final_refinement
python3 -m unittest discover -s tests -v
```

Both font files and cached masks are included. Rendering uses Cycles CPU, 64 samples,
denoising and eight threads; no particular GPU is assumed. Twenty host tests passed,
plus actual-Blender mesh, silhouette, occlusion, shader and saved-scene checks.
All eleven final PNGs were decoded and representative final renders and comparisons
were visually inspected. Pixel/parameter checks do not establish an exact match to
the real meter image, and human appearance approval is still required.

**Stop here. No protective glass, new randomized training data, diffusion or detector
training was added. Await explicit approval before proceeding.**
