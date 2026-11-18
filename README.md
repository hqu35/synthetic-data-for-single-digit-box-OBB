<!-- recursive-summary:start -->
## Directory overview

Research code for synthetic mechanical water-meter imagery, digit-strip geometry and prompt preparation. The 2.5D-named blurry worker uses Blender 3D. No model inference is performed by the prompt-preparation scripts.

Generated experiment and dataset trees are summarized at their `exp/` roots; VCS internals, caches and symlink targets outside the repository are excluded. Historical results are not active code.

## Getting started

- For the mask worker, see [geometry_worker](2D_Mask_for_Diffusion/2d_mask_4_diffusion_V1/geometry_worker/README.md).
- For a matched mask and prompt, see [Prompt_generator](Flux3_kelin_ComfyUI_workflow/Prompt_generator/README.md).
- For the Blender register, see [3D_worker](3D_worker/README.md).

### Files

| File | Role |
|---|---|
| [.DS\_Store](.DS_Store) | macOS Finder metadata. |
| [.gitignore](.gitignore) | Git ignore rules for generated artifacts and local caches. |
| [AGENTS.md](AGENTS.md) | Repository-wide instructions for agents and development tasks. |
| [README.md](README.md) | Directory documentation and this managed overview. |

### Subdirectories

| Directory | Role |
|---|---|
| [2.5D\_blurry\_4\_diffusion/](2.5D_blurry_4_diffusion/README.md) | Blender-based, heavily blurred and contaminated register image generator. It reuses the shared 3D scene and atlas. |
| [2D\_Mask\_for\_Diffusion/](2D_Mask_for_Diffusion/README.md) | V1 and V2 mask generation with FLUX rectangles and YOLO OBB labels. |
| [3D\_worker/](3D_worker/README.md) | Blender scene generation and historical review tools for the physical register, glass and annotations. |
| [Flux3\_kelin\_ComfyUI\_workflow/](Flux3_kelin_ComfyUI_workflow/README.md) | A saved ComfyUI workflow and separate scripts that prepare mask-conditioned prompt inputs; this directory does not itself prove successful model execution. |
| [shared/](shared/README.md) | Shared assets, configurations, implementation modules, tests, documentation, skills and delivery utilities. |

### Summary

This directory groups the files and subdirectories described above.

<!-- recursive-summary:end -->
