# 3D graphics worker

The shared 3D scene and scratch generation entry point are in [scene](scene/README.md). Existing experiments and scene dependencies live under `exp/`; `outputs` is a compatibility link to `exp`. Shared assets and modules live under `../shared/`.

## Semantic organization

- `effects/blur/`: blur-specific visual review.
- `effects/shear/`: X-shear comparison and OBB review.
- `effects/glass/`: glass scene and optics review scripts.
- `geometry/rolling/`: digit atlas, wheel size, rolling order, and gap review scripts.
- `experiments/glass_heavy_scratches_001/` and `experiments/glass_surface_noise_001/`: glass scratch and surface-noise implementations and experiments.
- `scene/`: shared 3D scene construction and scratch generation; these use shared geometry, materials and OBB logic.

The `2.5D_blurry_4_diffusion` worker uses this same 3D scene and existing OBB pipeline; blur does not require a separate OBB algorithm.
