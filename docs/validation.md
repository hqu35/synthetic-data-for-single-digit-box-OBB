# Initial end-to-end validation

Validated on October 28, 2026 (America/Chicago), using Blender 5.1.1,
Cycles CPU, host Python with Pillow 11.3, seed `20261028`.
The preview batch uses 16 samples per pixel and 640 × 320 RGB PNGs.

| Check | Final result |
| --- | --- |
| Successfully exported images | 50 |
| YOLO digit-slot OBBs | 270 |
| Positive / negative target rotations | 25 / 25 |
| Five-wheel / six-wheel registers | 30 / 20 |
| Rejected final-run attempts | 0 |
| Measured angle range | −19.582322° to +18.607312° |
| Minimum absolute measured angle | 2.552667° |
| Maximum requested/measured error | 0.282463° (limit 0.8°) |
| Maximum within-register angle spread | 0.560306° (limit 1°) |
| Stable / transitioning wheels | 156 / 114 |
| Sampled visible-gap ratio | 0.036271–0.195475 |
| Dark / ivory appearances | 31 / 19 |
| Perspective / orthographic images | 33 / 17 |
| Aperture coverage rays checked | 2,430 |

All 50 final PNGs were decoded, every saved label was independently reread,
all OBBs passed geometry, ordering, enclosure, count, range, angle and metadata
checks, and each aperture passed the image-contrast check. PNG and self-contained
SVG overlays use the exported label coordinates.

The complete contact sheet and representative full-resolution overlay
`000010.png` were visually inspected. Slots remain visible with correctly aligned
OBBs; both rotation signs, five/six-wheel layouts, light/dark/red wheels and
independently transitioning digits are represented.

## Rolling validation

The separate six-image fixed-scene sequence renders stable 3, 3→4 at
0.25/0.50/0.75, stable 4, and 9→0 at 0.50. Only the middle wheel changes.
All 36 labels passed the saved-file audit. Camera, lighting, materials, aperture
geometry and OBB coordinates were identical across the six states. The saved
rolling strip was visually inspected: the current numeral leaves downward and
its successor enters from above, including wraparound, without duplicated slot
annotations.

Eight standard-library unit tests passed, covering enclosing rectangles,
corner ordering, general perspective quads, degenerate geometry, exact label
round-trip, balanced reproducible sampling, invalid configuration and continuous
rolling direction/wraparound for all ten digits.

Real-Blender regression checks passed for five sampled scenes, including the
camera-calibration regression case. Every numeral mesh vertex was checked against
its cylindrical radius. Projected aperture OBBs remained unchanged through 250
digit/transition states (all ten digits, five fractions, five scenes).

## Reproduction and quality preset

Metadata replay of sample `000010` reproduced **identical decoded RGB pixels**
and byte-identical YOLO labels. The PNG files contain differing Blender render
timestamps/timings, so whole-file hashes differ. See `replay_check.json`.
Cross-version/platform pixel identity has not been tested.

The documented `run.py` wrapper was exercised end to end for the rolling
sequence and the higher-quality preset. A 1024 × 512, 96-sample CPU render passed
the saved-file audit; the complete high-quality 50-image batch was not run.

Development previews exposed camera-up and minimum-rectangle edge-selection
ambiguities; these were fixed before regenerating the final outputs. Earlier
diagnostic batches are retained under `outputs/development/` and are not part
of the deliverable dataset. The reference repository was only read.

## Artifacts

Paths below are relative to this report:

- [50-image dataset](/Users/ququ/Documents/Codex/2026-10-28/synthetic-data-for-single-digit-box-OBB/experiment_001_initial-blender-validation/results/)
- [Final contact sheet](/Users/ququ/Documents/Codex/2026-10-28/synthetic-data-for-single-digit-box-OBB/experiment_001_initial-blender-validation/results/validation/contact_sheet.png)
- [Machine-readable validation summary](/Users/ququ/Documents/Codex/2026-10-28/synthetic-data-for-single-digit-box-OBB/experiment_001_initial-blender-validation/results/validation/summary.json)
- [Replay comparison](/Users/ququ/Documents/Codex/2026-10-28/synthetic-data-for-single-digit-box-OBB/experiment_001_initial-blender-validation/results/validation/replay_check.json)
- [Six-state rolling strip](/Users/ququ/Documents/Codex/2026-10-28/synthetic-data-for-single-digit-box-OBB/experiment_001_initial-blender-validation/rolling/validation/rolling_sequence.png)
- [Rolling validation summary](/Users/ququ/Documents/Codex/2026-10-28/synthetic-data-for-single-digit-box-OBB/experiment_001_initial-blender-validation/rolling/validation/summary.json)
- [Higher-quality preview](/Users/ququ/Documents/Codex/2026-10-28/synthetic-data-for-single-digit-box-OBB/experiment_001_initial-blender-validation/quality/images/000000.png)

Generated outputs are intentionally excluded from Git by `.gitignore` and remain
available locally. Geometry source SHA-256 for these renders:
`149bfdd293e637d47955bd5126b861c026bf89f01758494a8ca4283afbf83563`.

This validates a functioning procedural geometry and annotation baseline.
Visual inspection is not a quantitative realism study. No real-image statistics,
pretrained detector training conventions, downstream accuracy, Linux runtime,
or cluster execution were validated. In particular, tight-glyph pretrained OBBs
must be checked for compatibility with this aperture/slot target before training.
