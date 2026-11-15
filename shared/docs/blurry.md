# 3D worker blur control

`--blur-percent` accepts a number from 0 to 50, inclusive. Zero adds no blur; increasing the value applies a wider Gaussian blur in linear RGB. At 1600 × 460, 50 corresponds to a Gaussian standard deviation of 4 pixels. The sigma scales with the smaller image dimension at other resolutions. This is an adjustable appearance parameter, not a measured percentage of lost resolution or a calibrated camera model.

The output PNG resolution and OBB coordinates remain unchanged. Sensor noise is a separate control, applied after blur; blur does not itself simulate noise. Existing camera processing remains active at 0, so 0 means no added blur, not removal of pre-existing blur or denoising.

For the 3D VLM worker, run from the repository root, choosing a new output directory:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python generate_vlm_exp.py -- --blur-percent 25 --output outputs/VLM_blur_25
```

The approved 3D experiment worker also accepts `--blur-percent 25`. Values outside 0–50 and non-finite values are rejected before rendering. Per-image metadata records the requested percentage and effective sigma. Five review images use one newly rendered 3D scene at 0, 12.5, 25, 37.5, and 50 percent, allowing the blur effect to be compared without changes in lighting, digits, or camera.

The five original-resolution review images are under `../outputs/blur_review/images/` and the comparison is `../outputs/blur_review/inspection_contact_sheet.png`. Labels are available in `../outputs/blur_review/labels/`; they describe numeral bands and are not corrected for glass refraction.

The 3D VLM worker now defaults to `--wheel-width-scale 0.75`, with 1200 × 460 output. Add `--wheel-width-scale 1.0` to reproduce the original register width and 1600 × 460 output. See [narrow wheel review](narrow_wheel_review.md).
