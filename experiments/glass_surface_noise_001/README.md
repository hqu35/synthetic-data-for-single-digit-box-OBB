# Glass scratches and surface noise

[Comparison sheet](results_refined/comparison_sheet.png) · [Five native-resolution renders](results_refined/images/) · [Close-up crops](results_refined/closeups/) · [Validation](results_refined/validation.json)

This controlled Blender/Cycles experiment uses the current 3D worker, photographic atlas, wheel geometry and upward rolling order. The five 1200 × 460 PNGs share the same fixed digit state, physical scene, camera, lighting, resolution, render seed and OBB projections. The lighting and approximately 19° yaw are taken from the recent blue-light batch. For evaluating the glass at target resolution, these are native Blender renders with no additional 50% camera blur or other image postprocessing.

The five cases are clean baseline, light scratches, moderate scratches, micro-roughness with faint broad variation, and a combined version. `config.json` controls the seed, scratch count, scratch strength, noise strength, samples and resolution. Set both strengths to zero for the existing clean glass. All five images and five OBB label files are in `results_refined/`. `results/` is the earlier exploratory comparison, which used longer and stronger scratches; it is retained for provenance and is not the recommended result.

## Method

Only a copy of the continuous glass material is changed. A seeded procedural surface mask is generated inside Blender from thin, tapered, slightly irregular curves of varied length and orientation. The mask controls local glass roughness and a very small bump-normal perturbation; it is not composited as ink or drawn on the final image. Blender noise nodes add micro-scale and broad, faint roughness variations for the noise cases. The original glass transmission and IOR are preserved. Scratches are most visible where the scene provides a reflection and may disappear at output scale. The close-ups use the same crop from each native image, enlarged 2× for inspection.

The initial stronger combined render looked noticeably scratched, so the final defaults were reduced. In the final sheet, light scratches and surface noise are very subtle at normal size; moderate scratches are the easiest to see. These images do not establish that the effect matches any real-world scratch distribution.

## Reproduce

Run from the repository root and choose a new output directory:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python experiments/glass_surface_noise_001/render.py -- --output /private/tmp/glass_surface_replay
python3 experiments/glass_surface_noise_001/make_comparison.py --input /private/tmp/glass_surface_replay
```

The worker requires the existing source scene `outputs/glass_review/protective_glass_review.blend`, its source parameters, the current worker code, and the current atlas assets/configuration. `fixed_sample.json` records the selected digit/camera/light parameters. The source atlas and scene are not modified by this experiment. Individual cases can be rendered by repeating `--case`, for example `--case 04_surface_noise --case 05_combined`.

## Validation and limits

Each case reloads the scene and compares the mesh geometry/transforms, camera matrix and lens, digit states, light settings and projected OBBs against the baseline before rendering. The worker's post-render image-processing pipeline was not used. In one clean-baseline replay the maximum pixel-channel difference was 1/255; the random masks are seeded, but multithreaded Cycles output is not guaranteed bitwise identical. Glass refraction is not fitted to the existing geometric OBB labels.
