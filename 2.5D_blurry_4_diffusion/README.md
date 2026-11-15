# Blurry register worker

`generate_degraded_register.py` uses the shared atlas and the 3D worker to render very blurry, dirty register images. It preserves perspective, rotation, and X-shear. The name describes the appearance, not the underlying renderer.

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python 2.5D_blurry_4_diffusion/generate_degraded_register.py -- --count 5 --output exp/my_new_batch
```

Run from the repository root; the relative output is resolved inside `2.5D_blurry_4_diffusion/`. Existing experiments are in `exp/`. Shared assets, configs, and digitgen modules are loaded directly from `../shared/`. The reused glass implementation is in `../3D_worker/experiments/`.

## OBB annotations

The worker reuses the 3D projected digit-strip contours, applies the same X shear to the image and contours, and refits a rectangular OBB for each strip. It writes five YOLO class-0 OBB labels per image in `labels/`, with per-image projection details in `metadata/`. Blur and low-resolution simulation preserve image coordinates. Labels represent geometric strips and do not correct for glass refraction.

The shared scene and scratch sampling are provided by `../3D_worker/scene/`.
