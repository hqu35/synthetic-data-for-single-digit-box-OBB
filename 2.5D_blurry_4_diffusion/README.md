<!-- recursive-summary:start -->
## Directory overview

Blender-based, heavily blurred and contaminated register image generator. It reuses the shared 3D scene and atlas.

The generator uses `3D_worker/scene` and the glass scratch implementation; its blur, low-resolution simulation and contamination are applied before writing image and OBB results.

From the repository root, use Blender with `--python 2.5D_blurry_4_diffusion/generate_degraded_register.py -- --count 1 --output exp/NEW_NAME`. The output path must be new.

### Files

| File | Role |
|---|---|
| [README.md](README.md) | Directory documentation and this managed overview. |
| [generate\_degraded\_register.py](generate_degraded_register.py) | Render heavily degraded 3D register photographs using existing scene and atlas. |
| [outputs](outputs) | Symbolic link to exp; no content is duplicated. |

### Subdirectories

| Directory | Role |
|---|---|
| [exp/](exp/README.md) | Historical blurry-register outputs, grouped here rather than documenting every generated sample. |

### Summary

This directory groups the files and subdirectories described above.

<!-- recursive-summary:end -->
