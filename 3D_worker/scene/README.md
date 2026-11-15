# Shared 3D scene

`scene_core.py` builds and configures the current Blender register scene and projects digit-strip geometry. `generate_scratch_multi.py` uses it to render the scratch dataset. The blurry diffusion worker imports these same components and applies its own image degradation and glass contamination. Their OBBs use the shared projected geometry and shear code.

From the repository root, to create a fresh scratch batch:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python 3D_worker/scene/generate_scratch_multi.py -- --output exp/my_new_scratch_batch
```
