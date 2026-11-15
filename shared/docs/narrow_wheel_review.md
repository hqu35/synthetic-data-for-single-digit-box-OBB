# Narrower 3D wheels and gaps

The 3D VLM worker now defaults to `--wheel-width-scale 0.75`. This scales the whole register along the wheel axle, including the five cylindrical wheels, their centers and spacing, dividers, frame, axle and glass. Consequently the wheel-band widths and intervening gaps are both 75% of their former widths. Wheel height and depth are unchanged. The horizontal scaling also makes the printed digits narrower, since they remain on the real curved surfaces.

The narrower register is rendered at 1200 × 460 by default instead of 1600 × 460, preserving the tight camera framing. The original can be requested with `--wheel-width-scale 1.0`. The existing `--blur-percent` setting remains available.

[Original and narrower comparison](../outputs/narrow_wheel_review/inspection_contact_sheet.png) · [Narrower render](../outputs/narrow_wheel_review/images/narrow_75_percent.png) · [Original render](../outputs/narrow_wheel_review/images/original.png) · [Measured geometry](../outputs/narrow_wheel_review/geometry_validation.json) · [OBB labels](../outputs/narrow_wheel_review/labels/)

Both views were rendered from the same digit states, camera parameters and lighting. Their lens fitting accounts for their different aspect ratios. The geometry check measures wheel-band width and the gap between neighboring numeral bands in world units; both ratios pass 0.75 within numerical tolerance. Five additional previous camera and digit states passed geometry projection and tight framing checks at the new default width. The two comparison renders each have five mesh-derived OBB labels. Glass refraction is not fitted to the labels.

Run a new batch from the repository root with a fresh output directory:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python generate_vlm_exp.py -- --wheel-width-scale 0.75 --blur-percent 25 --output outputs/VLM_narrow
```
