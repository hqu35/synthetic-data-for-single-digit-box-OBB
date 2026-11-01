# Rolling digit visible-gap review

[Measured comparison](../outputs/rolling_gap_review/inspection_contact_sheet.png) · [Numerical measurements](../outputs/rolling_gap_review/gap_measurements.json) · [All seven images](../outputs/rolling_gap_review/images/) · [OBB labels](../outputs/rolling_gap_review/labels/)

The 3D wheel and atlas were adjusted to reduce the visible blank space between successive printed digits. On a single 4-to-5 wheel, the same camera, lighting and geometry were rendered at several wheel rotations. The measurement is the number of blank image rows between the bottommost visible upper stroke and the topmost visible lower stroke, divided by the height of the projected physical digit-window OBB. It is not the distance between digit centers.

| Transition progress | Blank pixels | Projected box height | Gap / box height |
|---|---:|---:|---:|
| 25% | 32 | 280.68 px | 0.1140 |
| 50% | 33 | 280.68 px | 0.1176 |
| 75% | 33 | 280.68 px | 0.1176 |

All three measurements are within the requested 0.09–0.12 interval for this view. The test uses a fixed crop of the center wheel and a dark-ink RGB threshold on the final rendered images; its details and measured pixel boundaries are in `gap_measurements.json`. These values are near the upper limit: a one-pixel difference is approximately 0.0036 of box height. Antialiasing, threshold choice, reflection, perspective, glyph shapes and occlusion can change the measured result. This is not proof of the constraint for every digit pair, camera or light.

The stationary zero in the same rendered view occupies approximately 55.4% of the projected window width and 73.9% of its height. Because adjacent atlas glyphs are now more closely spaced, small slivers of neighboring digits are visible at some window edges even at 0% rotation; see `images/transition_000.png`. This is a real tradeoff in this configuration, not a fully isolated stationary digit. The atlas has ten positions with 36 degrees between centers and repeats from 9 to 0. The original font ink bounds are trimmed before sizing, and wheel radius was adjusted with the window and atlas to avoid merely elongating the digits.

The final settings are in `configs/rolling_numerals_atlas.json`; the 3D VLM worker loads them by default. The earlier horizontal scale and blur control remain available. The original and intermediate render batches remain separate.

`python3 measure_rolling_gap.py` regenerates the fixed-review measurement and comparison; it expects the seven review PNGs and metadata under `outputs/rolling_gap_review`. `python3 -m unittest tests.test_rolling_atlas tests.test_appearance` checks atlas layout and image processing. The results are inspection artifacts and require human review; they are not a real-image calibration or a general dataset-wide guarantee.
