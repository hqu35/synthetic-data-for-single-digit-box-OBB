<!-- recursive-summary:start -->
## Directory overview

NumPy/Pillow geometry sampler and renderer. Current output has five digit-strip regions and contains no digit identities.

Generate a batch from the repository root:

```sh
PYTHONPATH=2D_Mask_for_Diffusion/2d_mask_4_diffusion_V1 python3 -m geometry_worker generate --count 1 --seed 20261104 --output /private/tmp/meter-mask-example
```

Each sample contains `conditioning.png`, `geometry.json`, `flux_bboxes.json` and YOLO `annotations.txt`. FLUX boxes are `[top,left,bottom,right]` on 0–1000 and enclose the continuous strip boundary; YOLO OBB vertices are normalized to 0–1. Sampling ranges are provisional, not empirically calibrated. Reconstructing older geometry uses the current schema.

### Files

| File | Role |
|---|---|
| [README.md](README.md) | Directory documentation and this managed overview. |
| [\_\_init\_\_.py](__init__.py) | Minimal statistical geometry and OBB conditioning worker. |
| [\_\_main\_\_.py](__main__.py) | CLI: generate a deterministic batch or reconstruct one saved geometry. |
| [audit.py](audit.py) | Check the image dimensions and annotation formats of a saved batch. |
| [config.json](config.json) | Configuration for the worker or experiment in this directory. |
| [geometry.py](geometry.py) | Sample and validate quadratic strip geometry in pixel coordinates. |
| [render.py](render.py) | Render conditioning images and separate diagnostic overlays. |
| [worker.py](worker.py) | Deterministic statistical sampling and reconstructible 2D strip geometry. |

### Summary

This directory groups the files and subdirectories described above.

<!-- recursive-summary:end -->
