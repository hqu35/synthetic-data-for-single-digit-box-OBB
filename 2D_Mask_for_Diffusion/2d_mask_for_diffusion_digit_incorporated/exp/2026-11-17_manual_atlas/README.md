# Mask-scale photographic numeral atlas

Use `atlas.png` as a vertical RGBA strip, ordered 0 through 9. Each tile is
142 by 275 pixels. A full gray window spans approximately 306 vertical atlas
pixels; sample around `(digit + theta + 0.5) * 275`, wrapping vertically.
The 1200 by 460 reference mask and strip geometry come from the November 16
ComfyUI prompt experiment. The tile pitch includes measured inter-digit space.

`latest.json` is the 11:47 manual export; `earlier.json` is the 11:42 export.
The ten later measurements determine the population medians. The earlier first
image supplies a separately annotated 1, not another independent observation.
The hand-selected identities were read from the rectified photographic crops.
Digits 3, 5, 6, and 7 use the project's photographed reference strip instead.
Their sizes are estimates, not measurements of those four digits in this set.
`calibration.json` records dimensions and glyph sources. This is a small
empirical sample, not a fitted font or population-wide calibration.

Inspect `centered_01234.png`, `centered_56789.png`, and `rolling_21546.png`.
The rolling preview uses theta 0.7 in slots two and four. Rebuild from the
repository root with `python3 2D_Mask_for_Diffusion/2d_mask_for_diffusion_digit_incorporated/build_measured_atlas.py`.
