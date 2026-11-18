# Digit-incorporated mask experiment

This worker reads an existing mask and geometry, then draws the shared
photographic atlas onto each center strip. Theta 0 centers the given digit;
theta 1 centers its successor modulo 10. The digits move upward as theta
increases. This is a 2D texture projection, not a physical 3D drum.

Example from the repository root:

```sh
python3 2D_Mask_for_Diffusion/2d_mask_for_diffusion_digit_incorporated/generate.py --mask-dir Flux3_kelin_ComfyUI_dependencies/Prompt_generator/Prompt_Generator_EXP_ComfyUI_2026-11-16/mask --output /private/tmp/digit-mask.png --digits 56789 --theta 0.5
```

The example uses the existing five-window mask; its historical geometry is
unchanged. For a different mask, supply its directory with `--mask-dir`.
