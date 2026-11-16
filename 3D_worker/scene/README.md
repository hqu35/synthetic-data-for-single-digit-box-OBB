<!-- recursive-summary:start -->
## Directory overview

Shared Blender scene setup and scratch-batch generation. The blurry worker imports this package.

From the repository root, the scratch generator can be run with Blender using `--python 3D_worker/scene/generate_scratch_multi.py -- --output exp/NEW_NAME`. It requires the shared assets and the saved glass scene under `3D_worker/exp/glass_review/`.

### Files

| File | Role |
|---|---|
| [README.md](README.md) | Directory documentation and this managed overview. |
| [\_\_init\_\_.py](__init__.py) | Shared 3D scene setup and scratch generation. |
| [generate\_scratch\_multi.py](generate_scratch_multi.py) | Render 20 varied 3D register images with glass scratches. |
| [scene\_core.py](scene_core.py) | Shared 3D scene setup, camera sampling and projection. |

### Summary

This directory groups the files and subdirectories described above.

<!-- recursive-summary:end -->
