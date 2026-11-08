# X-only shear for the 3D graphics worker

The 3D VLM and scratch generators apply a deterministic image-space horizontal affine shear to the rendered image and its projected digit-strip contours. No Y shear is applied. The pixel-coordinate mapping, including a centering translation and any protective padding, is `x_out = x + s*(y-height/2) + pad`, `y_out = y`. This is the requested X shear up to a horizontal translation. It is a 2D augmentation after Blender rendering, not a new 3D camera pose.

For each batch, stratified sampling assigns approximately 50% of samples to `s` uniformly sampled from [-0.03, 0.03], 30% to [-0.08, 0.08], and 20% to [-0.12, 0.12]. For 20 samples the assignment is exactly 10, 6, and 4. These ranges overlap: the percentages describe selected ranges, not distinct observed absolute-magnitude bands. The assignments and values are reproducible from the seeds. Both generators enable shear by default; pass `--no-shear` to disable it.

The projected mesh boundary is transformed with the same affine and a minimum-area rectangular OBB is fitted again in pixel coordinates. Metadata records the shear, affine, original projection, pre-shear framing, and transformed projection. The camera matrix is the original Blender camera; glass refraction is not corrected in annotations. The existing image width is retained if the transformed register and annotations fit; otherwise symmetric horizontal padding is added. Peripheral background can be cropped and edge pixels are replicated in newly exposed areas. No scene geometry, typography, or digit ordering is altered by this augmentation.

## Comparison

[Six signed-strength examples with OBB overlays](../outputs/x_shear_review_adaptive_2026-11-07/contact_sheet.png) use the same existing 3D Blender image, transformed with six explicit coefficients; they are not six independent Blender renders. The unannotated images, overlays, labels, and metadata are in the corresponding results subdirectories. All six retain the original 1200-pixel width and a register fraction of approximately 90.05%.

A frozen reproduction of the comparison and its input is included under `reproduction/`. The review runs with `python3 render_x_shear_review.py` in that folder. To generate new images with Blender, for example:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python generate_vlm_exp.py -- --count 20 --seed-base 2026110703 --output outputs/my_new_shear_batch
```

Run from the repository root and use a fresh output path. For the scratch worker substitute `--python generate_scratch_multi.py -- --output outputs/my_new_scratch_batch`.

## Validation

Eight unit tests passed, including sampling, coordinate mapping, raster motion, canvas protection, rectangle containment, and rolling atlas behavior. One Blender render was completed through each updated worker and checked for dimensions, image checksum, five labels, and consistency between transformed contours and metadata. The existing 20-image scratch dataset was checked read-only; it remains valid without shear metadata. These smoke tests do not constitute a new full dataset or certify visual realism or refractive accuracy.
