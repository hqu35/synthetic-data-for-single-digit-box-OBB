# Mechanical, UV, material and camera upgrade validation

Validated October 29, 2026 (America/Chicago) on Blender 5.1.1, Cycles CPU,
preview seed 20261028, 640 × 320 RGB, 16 samples/pixel with denoising.
The original source and earlier outputs were preserved; the upgraded training
batch is `outputs/upgrade50`.

| Check | Result |
| --- | --- |
| Successful final images | 50 |
| Saved-label OBBs | 279 |
| Positive / negative targets | 25 / 25 |
| Five-wheel / six-wheel registers | 21 / 29 |
| Rejected attempts, explicitly regenerated | 7 |
| Measured angle range | −19.831868° to +19.790266° |
| Minimum absolute measured angle | 2.105412° |
| Maximum requested/measured error | 0.219428° (limit 0.8°) |
| Maximum within-register spread | 0.415833° (limit 1°) |
| Accepted gap-ratio range | 0.039715–0.192360 |
| Stable / transitional wheels | 161 / 118 |
| Neutral / cool-blue / warm images | 20 / 15 / 15 |
| 20-pin / 30-pin registers | 31 / 19 |
| Total modeled pins | 6630 |
| Orthographic / perspective images | 23 / 27 |
| Maximum color-clipped channel fraction | 0.00234538 (limit 0.03) |
| Wheel-coverage rays checked | 2511 |

Every PNG was decoded, every label reread, and geometry/count/order/angle/enclosure,
state, material/asset metadata, physical envelope, pin count, and raw/final pixel
dimensions checked. All final images passed aperture contrast checks. Overlays
read saved labels rather than independently recomputing their boxes.

The seven failed attempts involved narrow apertures/gaps under perspective exposing
an axial wheel edge. Coverage checks rejected them before export, and regeneration
produced 50 successes. The accepted gap/camera distribution is therefore conditioned
on visibility; it is not a claim of unrestricted independent uniform parameters.
See `validation/failures.json` for every rejected index, attempt, seed and reason.

## Geometry and printed texture

The assembly is constructed from actual cylindrical body/rim/pin meshes with bevels,
a shared stationary axle, and solid frame/separators. Body ink is a periodic
cylindrical UV texture, without raised text geometry. The diagnostic suite includes
an exposed oblique assembly, pin close-up and packed `assembly.blend`. Pins are
short under the small-gap defaults; dimensions can be tuned together with clearance.

Two stable-digit calibration renders cover 0–9. Visual inspection confirmed upright,
unmirrored digits and correct surface wrapping. Automated tests reconstruct every
stable print from the UV mapping and compare it with the upright source font. The
atlas seam has zero ink at both edges.

## Shader and photographic comparisons

The guide and subsequently supplied tutorial screenshots were inspected. Actual
Blender node checks verify the shared Generated/Mapping coordinate chain, all three
noise settings/types, Math Multiply, inverted Bump, and the reference bump settings
of strength 0.05 / distance 1.0. The cream preset reduces bump distance to 0.004 and
strength to 0.01–0.025, and remaps roughness to 0.55–0.80; this deliberate scale
adaptation is documented in [shader notes](shader.md).

Basic, reference-dark and cream presets were rendered with identical geometry,
camera and lights; the side-by-side sheet was visually inspected. Cream/basic ink
is dark, while the reference-dark preset uses pale ink. The three camera presets
keep physical scene/material parameters exactly equal. Raw rerenders differed by
at most one 8-bit channel level at 35 of 524,288 pixels, consistent with minor
multi-threaded renderer rounding. The cool/warm appearance is introduced by the
independent photographic transform, without recoloring the cream material.

## Rolling, tests and reproduction

Six fixed-scene renders show stable 3, 3→4 at 0.25/0.50/0.75, stable 4, and 9→0
at 0.50. All 36 OBBs passed the saved-artifact audit. The OBB coordinates remain
exactly identical across the sequence. Visual inspection confirmed the current
digit moving downward and its successor entering from above.

**14 host tests passed**, covering geometry, clearance, sampling groups, UV/font
orientation, seam, PNG round-trip, seeded camera effects and color/material
separation. Actual-Blender tests passed shader/UV/pin checks and **250 wheel-state
OBB-invariance cases**, including all ten digits near their wrap endpoints.

Metadata replay of accepted sample 000024, originally accepted on attempt 2,
reproduced identical sampled/resolved parameters and byte-identical labels.
RGB differed at **20 of 204800 pixels** by at most **one 8-bit level**;
this is near-identical rendering, not exact image-byte reproducibility. The largest
per-channel RMS difference is 0.00765466 on the 0–255 scale.
These measurements are saved in `validation/replay_check.json`.

A 1024 × 512, 96-sample CPU image using the final-quality preset passed audit and
was visually inspected. The full high-quality batch was not run. Linux/CHTC
execution and downstream detector training were not tested.

## Review artifacts

- [50-image contact sheet](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_002_uv-mechanics-material-upgrade/results/validation/contact_sheet.png)
- [Final machine-readable audit](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_002_uv-mechanics-material-upgrade/results/validation/summary.json)
- [Rejected attempts](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_002_uv-mechanics-material-upgrade/results/validation/failures.json)
- [Replay measurement](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_002_uv-mechanics-material-upgrade/results/validation/replay_check.json)
- [Exposed assembly](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_002_uv-mechanics-material-upgrade/diagnostics/inspection/exposed.png)
- [Pin close-up](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_002_uv-mechanics-material-upgrade/diagnostics/inspection/pin_detail.png)
- [Packed Blender scene](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_002_uv-mechanics-material-upgrade/diagnostics/inspection/assembly.blend)
- [Material comparison](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_002_uv-mechanics-material-upgrade/diagnostics/material_comparison.png)
- [Camera comparison](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_002_uv-mechanics-material-upgrade/diagnostics/camera_comparison.png)
- [All ten stable UV digits](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_002_uv-mechanics-material-upgrade/diagnostics/uv_calibration.png)
- [Rolling sequence](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_002_uv-mechanics-material-upgrade/rolling/validation/rolling_sequence.png)
- [High-quality preview](/Users/ququ/Documents/Codex/2026-10-29/synthetic-data-for-single-digit-box-OBB/experiment_002_uv-mechanics-material-upgrade/quality/images/000000.png)

The requested four mechanical/real-register reference photographs were not present
in the accessible attachments or identified by a local path. The user subsequently
provided shader-tutorial screenshots, which were inspected. Direct matching to the
four mechanical photographs remains unverified. The procedural images are a
working technical baseline, not an empirically established photorealistic match.
Digit-slot targets also remain unverified against any pretrained tight-glyph labels.

Generated outputs are local and Git-ignored; source, configuration, cached atlas,
font and its OFL license are in the repository. Core source SHA-256:
`9b4ae97d27536f596324cb913abe07f9cf793f4ae6d875ae14e040aae8d51b5b`.
