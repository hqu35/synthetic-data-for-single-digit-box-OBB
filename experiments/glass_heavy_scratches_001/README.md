# Heavy glass scratches

[Clean vs. heavy comparison](results/comparison_sheet.png) · [Heavy render](results/images/02_heavy_scratches.png) · [Clean baseline](results/images/01_clean_baseline.png) · [Inspectable Blender scene](results/heavy_scratch_scene.blend) · [Close-ups](results/closeups/) · [Validation](results/validation.json)

This is a separate heavier-damage variant of the preceding glass experiment. Both 1200 × 460 renders use identical digit states, geometry, camera, lighting, resolution, render seed and OBBs. The heavy case uses 95 seeded hairlines of varied lengths and directions. A generated mask drives roughness and a small bump perturbation of the actual Blender glass material; no scratches are drawn on the rendered image or on the digit wheels. The count and strength can be changed in `config.json`. The heavy render uses no added post-render blur.

The packed `.blend` contains the heavy-scratch glass material and generated mask and can be opened for inspection. The scratches are deliberately more visible than in the light/moderate experiment; matching the frequency or appearance of real heavy scratches requires comparison with real images.

## Reproduce

From the repository root, choose a new output folder:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python experiments/glass_heavy_scratches_001/render.py -- --output /private/tmp/glass_heavy_replay
python3 experiments/glass_heavy_scratches_001/make_comparison.py --input /private/tmp/glass_heavy_replay
```

`save_scene.py` constructs the packed Blender scene in `results/`; do not rerun it against the existing file if it must be preserved. The render script requires the existing worker, source glass scene and current photo atlas. All random patterns are seeded, although multithreaded Cycles rendering need not be bitwise identical.
