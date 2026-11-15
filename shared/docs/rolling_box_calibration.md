# Digit window and rolling-atlas calibration

[Transition comparison](../outputs/rolling_box_calibrated/inspection_contact_sheet.png) · [Original-resolution images](../outputs/rolling_box_calibrated/images/) · [OBB labels](../outputs/rolling_box_calibrated/labels/) · [Numerical validation](../outputs/rolling_box_calibrated/validation.json)

The 3D worker uses ten atlas tiles around one complete cylindrical wheel. Each digit position is 36 degrees apart; transition progress 0 means the current digit is centered, and 1 means the next digit is centered. The atlas repeats across the 9-to-0 seam. The revised atlas sizes the actual ink, accounting for font side bearings, instead of stretching the visible numeral to fill the window.

The digit-window height is reduced from 0.740 to 0.675 geometry units. Each wheel's radial dimensions are 85% of the earlier radius and its axle is moved forward so the front printed surface retains its previous clearance to the glass. Window frame components are scaled vertically around their center. The previously requested 75% horizontal register scaling remains active. The atlas and geometry configuration is `configs/rolling_numerals_atlas.json`.

For the stationary zero in the review render, a thresholded ink bounding box measures 54.9% of the projected window width and 73.9% of its height. This is a single rendered view and approximate image-space measurement; glyph shapes, perspective, reflections and glass can affect apparent fractions. The mask and geometric design target approximately 55% and 75%, respectively. Other numerals retain their font-specific widths.

Five images show the same 4-to-5 transition at 0%, 10%, 20%, 50% and 100%. In this camera view a portion of the incoming 5 is visible at 20%; it is not clearly visible at 10%. Visibility at other angles and for other glyphs is not guaranteed by this one render. The review images include mesh-derived digit-band OBB labels; glass refraction is not fitted to those labels.

The width and height are the camera image dimensions of the ink relative to the physical digit-window aperture, not the digit-band OBB. All five images are 1200 × 460. Five further prior camera and digit configurations passed geometry projection and tight-framing checks without rendering.

To run the updated 3D worker, choose a fresh output directory:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python generate_vlm_exp.py -- --wheel-width-scale 0.75 --blur-percent 0 --output outputs/VLM_new
```

`python3 -m unittest tests.test_rolling_atlas tests.test_appearance` checks atlas tile placement, seam spacing, measured geometry targets, blur and image processing. The visible results still require human judgment.
