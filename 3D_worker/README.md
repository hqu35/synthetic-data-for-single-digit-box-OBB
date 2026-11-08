# 3D graphics worker

3D renderers and review scripts live here. `generate_vlm_exp.py` and `generate_scratch_multi.py` are primary batch entry points. Existing experiments and scene dependencies live under `exp/`. `outputs` is a compatibility link to `exp`; `assets`, `configs`, and `digitgen` point to shared components.

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python 3D_worker/generate_vlm_exp.py -- --count 1 --output exp/my_new_batch
```

Run from the repository root; the relative output path is resolved within `3D_worker/`. Material-experiment code remains in `experiments/`; its results are in `exp/material_experiments/` with compatibility links.
