# 2D mask and annotation worker

`geometry_worker/` is the standalone statistical digit-strip geometry and dual FLUX AABB / YOLO OBB conditioning worker. It is independent of Blender. Existing annotation and geometry experiments are in `exp/`. See `geometry_worker/README.md` for algorithms, assumptions and audit details.

```sh
PYTHONPATH=2d_mask_4_diffusion python3 -m geometry_worker generate --count 20 --seed 20261104 --reading 43882 --output 2d_mask_4_diffusion/exp/my_new_batch
PYTHONPATH=2d_mask_4_diffusion python3 -m geometry_worker.audit 2d_mask_4_diffusion/exp/my_new_batch
```

Run these commands from the repository root; the `PYTHONPATH` setting finds the worker in this directory.

New outputs provide `flux_bboxes.json` with integer `[top, left, bottom, right]` boxes on 0–1000 and `annotations.txt` with the original four YOLO OBB vertices normalized to 0–1. Both use the entire image.
