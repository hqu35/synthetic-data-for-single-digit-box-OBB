# 2D mask and annotation worker

`geometry_worker/` is the standalone statistical digit-strip geometry and AABB conditioning worker. It is independent of Blender. Existing annotation and geometry experiments are in `exp/`. See `geometry_worker/README.md` for algorithms, assumptions and audit details.

```sh
PYTHONPATH=2d_mask_4_diffusion python3 -m geometry_worker generate --count 20 --seed 20261104 --reading 43882 --output 2d_mask_4_diffusion/exp/my_new_batch
PYTHONPATH=2d_mask_4_diffusion python3 -m geometry_worker.audit 2d_mask_4_diffusion/exp/my_new_batch
```

Run these commands from the repository root; the `PYTHONPATH` setting finds the worker in this directory.

New outputs use normalized `[xmin, ymin, xmax, ymax]` AABBs in `aabb.json`; `annotations.txt` adds the class ID before those four values. They are based on the full output image. Previous OBB datasets are not modified.
