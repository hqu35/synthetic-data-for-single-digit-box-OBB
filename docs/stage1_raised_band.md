# Stage 1 revision: narrow raised bands and edge-mounted pins

**Stop condition: geometry inspection only; explicit approval is required before Stage 2.**
The fixed states remain `00054`, with only the last wheel at a 0.05 early 4→5
transition. No glass, new shader system, randomization or training dataset was
implemented. Prior inspection scenes and images remain available.

## Mechanical reconstruction

The old full-width printed drum is replaced by three physically distinct parts:
a wider recessed solid base, an annular raised UV-printed band, and an annular
right-edge collar carrying the pins. The band has an inner cylindrical wall,
outer cylindrical wall, and two closed annular shoulders. It is not an overlapping
solid cylinder or a planar decal. The same cream plastic graph and font are used.

| Quantity | Actual fixed value |
| --- | ---: |
| Base radius `R_base` | 1.10 |
| Numeral-band radius `R_band` | 1.25 |
| Raised radial step | 0.15 |
| Base axial width | 0.62 |
| Old band width | 0.82 |
| `band_width_scale` | 0.625 |
| New band axial width | 0.5125 |
| Total slot width | 0.640625 |
| `band_to_slot_ratio` | 0.80 |
| Left slot margin | 0.025625 |
| Right slot margin | 0.102500 |
| Band left/right local X | −0.2946875 / +0.2178125 |
| Band center local X | −0.0384375 |
| Band-edge collar axial width | 0.015 |
| Collar outer radius | 1.265 |
| Pin root/tip local X | +0.2328125 / +0.3053125 |
| Pin center local X | +0.2690625 |
| Pin radial center | 1.225 |
| Pin radius/axial length | 0.035 / 0.0725 |
| Pin density | 2 per numeral interval; 20 per wheel |
| Digit gap ratio `g / slot_width` | 0.12 |
| Visible inter-slot gap | 0.076875 |
| Uniform center pitch | 0.717500 |
| Complete physical axial envelope | 0.620000 |
| Free clearance between assemblies | 0.097500 |

The spare slot width is allocated 20% left / 80% right. Pin shafts extend from the
band-edge collar into the right margin, above the recessed base. Their minimum
radial extent is 1.190, leaving 0.090 radial clearance above the 1.10 base. Pins
share their band's axle parent and have real beveled cylindrical meshes.

Spacing is derived once: `pitch = slot_width * (1 + digit_gap_ratio)`. Physical
clearance is measured from the complete part envelope; pin length is not added to
pitch again because these pins fit inside the wider drum's axial envelope. This
preserves the gap-ratio meaning while separating band, slot, base and pitch.
The new 0.12 value is a fixed review setting, not a claim that the previous review
scene's numerical gap was retained.

## Fixed viewing and comparison controls

The near-frontal single-slot view is the primary acceptance image. Its right side
shows actual pin shafts and a recessed curved base, with local shadows. The full
row uses stationary separators only between slots; its within-slot side regions
are actual wheel geometry, not flat filler panels.

All light positions, energy, size, plastic settings, wheel states and font identity
remain those of the preceding fixed inspection. Cameras retain the same general
front/oblique setup, with framing adjusted for the smaller model. The before/after
single-slot comparison freezes the **same camera matrix, lens, resolution, lights
and material parameters** for both geometries. Only the construction changes.

A higher-resolution mask (10,240 × 1,024) was rasterized from the same font with
unchanged normalized numeral dimensions, to avoid pixelation in the large close-up.
Both before and after use this same texture asset. The plastic node graph was not
modified. The exploded view temporarily separates the real base, band and collar/
pins along X; assembled positions are restored before the other views and .blend
are saved.

## Reproduce

From the repository root, use a new/empty output directory:

```bash
python3 -c 'import json; from prepare_assets import prepare; prepare(json.load(open("configs/stage1_raised_band.json")))'
"/Applications/Blender.app/Contents/MacOS/Blender" \
  --background --factory-startup --python-exit-code 1 \
  --python stage1_raised_band.py -- \
  --config configs/stage1_raised_band.json \
  --output outputs/stage1_raised_band
python3 review_raised_stage1.py outputs/stage1_raised_band
```

The high-resolution atlas is already cached in the repository. Replace the macOS
executable with `blender` on PATH if appropriate. Rendering was tested with Blender
5.1.1 / Cycles CPU / 64 samples; Linux was not runtime-tested.

## Review artifacts

- [A — Single-wheel exploded components](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/A_exploded.png)
- [B — Primary single-digit front close-up](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/B_single_digit_front.png)
- [C — Two-wheel clearance view](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/C_two_wheel.png)
- [D — Five-wheel near-frontal view](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/D_five_wheel_front.png)
- [E — Three-quarter assembled view](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/E_three_quarter.png)
- [F — Matched before/after comparison](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/F_before_after_comparison.png)
- [Supplemental cool front](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/D_front_cool.png)
- [Five test slot OBBs over the final RGB](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/D_front_test_obb_overlay.png)
- [Test labels](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/test_slot_obbs.txt)
- [Contact sheet](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/inspection_contact_sheet.png)
- [Packed assembled Blender scene](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/raised_band_assembly.blend)
- [Actual geometry checks](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/geometry_checks.json)
- [Configuration, views and geometry report](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/inspection_report.json)
- [Saved-artifact audit](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_004_stage1-raised-band/results/artifact_audit.json)

## Verification

Blender checks closed/manifold annular meshes, positive signed volume, two actual
band radii, parent attachment and rotation, correct pin count/root position,
containment within the right slot margin, and evaluated neighboring part clearance.
Base/band and base/collar meet at shared cylindrical interfaces. Collar/band and
pin bases meet at axial faces; these mounting contacts are intentional. Pin shafts
clear the underlying base, and neighboring assembly envelopes do not intersect.

The important front-view check casts a camera ray toward the center wheel's front
pin: the first hit must be the actual `wheel_2_pin_00` shaft. It cannot pass merely
because pins exist somewhere in the scene. Visual inspection still determines
whether the rendered construction meets the intended geometry.

Seventeen host regression tests passed, including new exact width/slot/margin,
edge-root, radial clearance and invalid-layout tests. The artifact auditor decodes
every saved view, checks matched comparison controls, and rereads the **five** test
OBBs from the exported text. Overlays use those saved coordinates. The existing
projection, solid-aperture intersection, minimum-area rectangle and YOLO polygon
export helpers are reused. No OBB pipeline redesign was introduced.

The diagnostic OBB remains **one complete physical slot aperture**, encompassing
its narrower band and the visible recessed/edge-mechanism regions. It is not a
band-only or tight-glyph label. This fixed near-frontal test does not enforce the
training generator's nonzero-angle distribution.

**Stage 1 ends here. Await explicit human approval before glass, further appearance
work or training-oriented synthetic generation.**
