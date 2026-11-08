# Blurry register worker

`generate_degraded_register.py` uses the shared atlas and the 3D worker to render very blurry, dirty register images. It preserves perspective, rotation, and X-shear. The name describes the appearance, not the underlying renderer.

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python 2D_blurry/generate_degraded_register.py -- --count 5 --output exp/my_new_batch
```

Run from the repository root; the relative output is resolved inside `2D_blurry/`. Existing experiments are in `exp/`. `assets`, `configs`, `digitgen`, and `experiments` are links to reused components.
