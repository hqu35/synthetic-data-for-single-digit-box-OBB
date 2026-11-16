# Diffusion mask worker V2

V2 reuses the V1 geometry and annotation functions. Each white window
contains a centered gray strip. The strip occupies 70% of the window width,
leaving 15% on each side. Adjacent black gaps are sampled at 1.25–1.75%
of window width, and curvature is lower than V1. Five and six windows are
supported.

Both YOLO OBB and FLUX AABB annotations target the gray strips. The FLUX
boxes are integer coordinates in `[top, left, bottom, right]` order on a
0–1000 grid; YOLO OBB vertices are normalized to 0–1. Digit identities
and rolling states are chosen independently by the prompt generator.

Geometry uses locally affine strips with perspective-inspired per-window
scaling. It is not an exact projective warp.

From the repository root, generate a mask and corresponding prompt:

```sh
python3 Flux3_kelin_ComfyUI_workflow/Prompt_generator/watermeter_generate_layout_prompt.py --output /private/tmp/meter-v2 --mask-version v2 --windows 6 --mask-seed 20261116 --prompt-seed 539
```

For a mask without a prompt:

```sh
PYTHONPATH=2D_Mask_for_Diffusion/2d_mask_4_diffusion_V2 python3 -m mask_v2 --output /private/tmp/meter-mask-v2 --seed 20261116 --windows 5
```

The [review examples](exp/2026-11-16_01-23-08_nested-mask-review/) contain
five- and six-window masks, annotation previews, labels, and prompts.
