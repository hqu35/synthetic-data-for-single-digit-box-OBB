<!-- recursive-summary:start -->
## Directory overview

Blender scene generation and historical review tools for the physical register, glass and annotations.

### Files

| File | Role |
|---|---|
| [README.md](README.md) | Directory documentation and this managed overview. |
| [diffusion\_model\_dataset](diffusion_model_dataset) | Symbolic link to exp/diffusion_model_dataset; no content is duplicated. |
| [font\_candidates.py](font_candidates.py) | Open industrial-font candidates; resolve before atlas hashing or rendering. |
| [generate.py](generate.py) | blender --background --factory-startup --python generate.py -- --config configs/preview.json |
| [generate\_diffusion\_exp1.py](generate_diffusion_exp1.py) | Generate the approved fixed-identity controlled experiment, then stop. |
| [obb\_band\_stage1.py](obb_band_stage1.py) | One unchanged reference RGB with corrected 3D numeral-band OBBs. Stop after review. |
| [outputs](outputs) | Symbolic link to exp; no content is duplicated. |
| [prepare\_assets.py](prepare_assets.py) | Build a seamless cylindrical ink mask with an openly licensed font (host Python). |
| [render\_diagnostics.py](render_diagnostics.py) | Native Blender diagnostic suite: exposed mechanics, shader comparisons and UV calibration. |
| [render\_tight\_framing\_preview.py](render_tight_framing_preview.py) | Render one tightly framed register preview; never resume the dataset batch. |
| [review\_band\_stage1.py](review_band_stage1.py) | Audit the single saved sample and create overlays from the exact exported labels. |
| [review\_diagnostics.py](review_diagnostics.py) | Audit diagnostic labels and create comparable material/camera/UV sheets. |
| [review\_tight\_framing\_preview.py](review_tight_framing_preview.py) | Inspect the saved single preview and create a separate label overlay. |
| [run.py](run.py) | Host-Python entry point: render with Blender, then audit saved files. |
| [stage1\_final\_refinement.py](stage1_final_refinement.py) | Final Stage 1 fixed pin/typography/ink review; never runs a dataset batch. |
| [stage1\_geometry.py](stage1_geometry.py) | STAGE 1 ONLY: fixed mechanical inspection. Never generates training labels/data. |
| [stage1\_raised\_band.py](stage1_raised_band.py) | Fixed raised-band geometry review ONLY. One five-slot diagnostic OBB overlay. |
| [validate.py](validate.py) | Independent saved-artifact audit and PNG overlays. Requires Pillow. |
| [validate\_diffusion\_exp1.py](validate_diffusion_exp1.py) | Validate every Experiment 1 pair and create English review previews. |
| [validate\_scratch\_multi.py](validate_scratch_multi.py) | Validate the finished 20-image scratch batch and build an overview. |
| [verify\_final\_stage1\_scene.py](verify_final_stage1_scene.py) | Reload the saved review .blend and verify actual shader and rolling OBB invariance. |

### Subdirectories

| Directory | Role |
|---|---|
| [effects/](effects/README.md) | Visual-effect review scripts grouped by physical effect. |
| [exp/](exp/README.md) | Historical renders, saved Blender scenes, comparison datasets and other experiment outputs. The glass scene remains a runtime dependency of current Blender workers. |
| [experiments/](experiments/README.md) | Source and configurations for Blender glass-surface experiments; result links point to historical outputs. |
| [geometry/](geometry/README.md) | Geometry-specific visual review scripts. |
| [scene/](scene/README.md) | Shared Blender scene setup and scratch-batch generation. The blurry worker imports this package. |

### Summary

This directory groups the files and subdirectories described above.

<!-- recursive-summary:end -->
