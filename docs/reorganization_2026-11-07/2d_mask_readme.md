# 2D mask and annotation worker

`geometry_worker/` is the standalone statistical digit-strip geometry and OBB conditioning worker. It is independent of Blender. Existing annotation and geometry experiments are in `exp/`. See `geometry_worker/README.md` for algorithms, assumptions and audit details.

```sh
python3 -m geometry_worker generate --count 20 --seed 20261104 --reading 43882 --output 2d_mask/exp/my_new_batch
python3 -m geometry_worker.audit 2d_mask/exp/my_new_batch
```

Run these commands from the repository root; the root `geometry_worker` compatibility link resolves to this directory.
