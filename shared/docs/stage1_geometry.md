# Stage 1 mechanical geometry review

**Status: inspection delivered; human approval pending. Stop here before Stage 2.**
No training dataset, random render batch, new OBB export, detector training or
diffusion workflow was generated for this stage. Existing annotations and earlier
outputs are preserved. The fixed inspection scene is separate from the existing
training configuration.

## Structural corrections

The previous narrow-gap configuration restricted pin length to approximately
0.006–0.010 units and rim thickness to 0.004–0.006. At assembly scale these appeared
as surface dots. The fixed inspection model uses actual **0.22-unit pin shafts**,
**0.10-unit separate rims**, and **0.14-unit free clearance beyond each complete
body/rim/pin envelope**. Neighboring wheels no longer hide essentially all of the
pins. These review dimensions deliberately prioritize visible mechanics and are
not an assertion that they have been measured from the reference photograph.

Each of five independent wheels has:

| Feature | Fixed value |
| --- | --- |
| Body radius / axial width | 1.25 / 0.82 |
| Body radial segments | 192 |
| Rounded outer edge | Bevel width 0.018 |
| Right rim radius / thickness | 1.20 / 0.10 |
| Pin density | 2 per numeral interval, 20 per wheel |
| Pin radius / protrusion past rim | 0.055 / 0.22 |
| Pin radial placement / bevel | 1.075 / 0.008 |
| Complete assembly axial width | 1.14 |
| Adjacent free clearance | 0.14 |
| Center pitch | 1.28 |
| Common axle radius | 0.13 |

The cylindrical body carries periodic UV-printed ink, not extruded numerals or
billboards. Wheel states are fixed at `00054`, with the final wheel at `4 → 5`,
progress 0.05. Each body, hub, rim and set of pins shares one axle parent. Pin axes
are parallel to local +X. Rims use a separate compatible plastic tint; pin material
is slightly darker/satin so cylinder ends and shaft highlights remain readable.
The existing guide-based cream plastic shader was retained.

`digitgen/mechanics.py` now accepts `include_frame=False` for a genuinely exposed
assembly, supports distinct inspection rim/pin materials, and checks complete
mechanical envelopes before construction. Existing callers retain the frame by
default. No annotation code was redesigned. Only the near-frontal view uses a thin
0.045-unit dark aperture lip, with a light surrounding mask; all exposed, pin and
grazing views hide the viewing mask.

## Reproduce only the inspection

From the repository root, on this macOS installation:

```bash
"/Applications/Blender.app/Contents/MacOS/Blender" \
  --background --factory-startup --python-exit-code 1 \
  --python stage1_geometry.py -- \
  --config configs/stage1_geometry.json \
  --output outputs/stage1_geometry --debug
python3 review_stage1.py outputs/stage1_geometry
```

Use a new or empty output directory for another run. On Linux replace the quoted
Blender executable with `blender`; Linux execution has not been tested. The included
font and cached ink texture make this fixed configuration self-contained. Blender
uses Cycles CPU, 64 samples per pixel, denoising and eight threads. There are no
random scene parameters, stochastic wheel states or automatic dataset calls.

Omit `--debug` to skip the extra topology render and debug .blend. The script saves
a clean `stage1_assembly.blend` with the full assembly exposed, neutral lights and
camera A active. Other named cameras and the front review mask remain available
for manual inspection. View-specific visibility is recorded in the report. The
numeral texture is packed into the .blend.

## Review images

All paths below point to the final inspection directory:

- [A — Complete three-quarter assembly](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/A_three_quarter_neutral.png)
- [B — Right-side pin and rim close-up](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/B_right_pin_closeup.png)
- [C — Near-frontal 00054 register](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/C_front_neutral.png)
- [D — Grazing curved-band inspection](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/D_grazing_curvature.png)
- [E — Same camera A under cool-blue illumination](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/E_three_quarter_cool_blue.png)
- [F — Same camera C under cool-blue illumination](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/F_front_cool_blue.png)
- [G — Actual mesh topology and wheel axes](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/G_topology_debug.png)
- [Assembly neutral/blue comparison](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/neutral_vs_blue_assembly.png)
- [Front neutral/blue comparison](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/neutral_vs_blue_front.png)
- [All-view contact sheet](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/inspection_contact_sheet.png)
- [Clean fixed Blender scene](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/stage1_assembly.blend)
- [Debug Blender scene](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/stage1_debug.blend)
- [Mechanical checks](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/geometry_checks.json)
- [Full parameters, cameras, lights, object names and hierarchy](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/inspection_report.json)
- [Saved-image audit](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_003_stage1-exposed-mechanics/results/artifact_audit.json)

The neutral/cool pairs use identical geometry, wheel states, camera matrices and
lens. Only light RGB changes; material remains cream `[0.76, 0.73, 0.63]`. Exposure
and view transform remain fixed. Cool appearance is illumination, not blue plastic.

## Verification and boundaries

Actual Blender mesh checks require five positive-width/radius cylindrical bodies,
192 curved side quads per body, circumference/axial UVs and positive bevels. They
check 20 pin meshes per wheel, their radial placement, shared rotating parent,
base attachment at the right rim face, and 0.22-unit axial extension beyond that
face. A temporary parent rotation verifies actual pin world motion and is restored
before rendering. Evaluated mesh envelopes verify 0.14 clearance between adjacent
assemblies, independent of visible digit-slot gaps.

The final-image audit decodes every PNG, verifies resolution and visible contrast,
compares neutral/cool camera/material settings, and checks that the output contains
no training-export directories. Fourteen existing host regression tests passed.
Successful script execution alone is not the acceptance criterion; the renders
are provided for human structural review.

The first grazing camera overemphasized the end cap and was corrected to view the
printed band from above at a shallow angle. Earlier inspection attempts are kept
separately in `outputs/stage1_geometry_first`. This is an inspection iteration,
not a random training batch.

The supplied `00054` cool real-register crop was visually inspected as a secondary
front-view/color reference. The exposed mechanical reference photograph still has
no accessible local path, so precise shape/proportion matching to that photo is
not claimed. The wider inspection spacing is intentional to make pin length and
inter-wheel clearance reviewable; tuning it for training is deferred.

**No Stage 2 work follows this script. Review the geometry and give explicit approval
before any training-oriented generation resumes.**
