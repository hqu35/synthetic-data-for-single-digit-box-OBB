# Stage 1 — corrected numeral-band OBB, one-sample approval checkpoint

Exactly **one deterministic `00054` RGB sample** has been rendered. There are exactly five exported OBBs, one per physical digit. The annotation now covers the central raised numeral-bearing band, including its cream background, rather than the entire slot or only black strokes. **Stage 2 is not started. Human approval is required before the 100-image Experiment 1 dataset.**

## Artifacts

- [Clean RGB — 000001.png](../outputs/obb_band_stage1/000001.png)
- [Same RGB with corrected OBB overlay](../outputs/obb_band_stage1/000001_overlay.png)
- [Full-slot versus corrected-band diagnostic](../outputs/obb_band_stage1/old_vs_corrected.png): orange = mesh-derived full slot; green = corrected band
- [Clean/overlay review sheet](../outputs/obb_band_stage1/inspection_contact_sheet.png)
- [YOLO-OBB labels — 000001.txt](../outputs/obb_band_stage1/000001.txt)
- [Geometry, camera, lighting, render parameters and projected boundaries](../outputs/obb_band_stage1/inspection_report.json)
- [Saved-artifact audit and measurements](../outputs/obb_band_stage1/artifact_validation.json)
- [Native saved scene](../outputs/obb_band_stage1/band_annotation_review.blend)
- [No-render multi-pose integration test log](../outputs/obb_band_stage1/band_projection_tests.log)
- [Frozen implementation and reproduction instructions](../outputs/obb_band_stage1/reproduction/README.md)

The orange diagnostic boxes reconstruct the former *full-slot semantics* from actual window meshes; they are not a claim that historical exported coordinates were correct. Clean RGB, overlays and diagnostic previews are separate files, all derived from the single render.

## Measurements and semantic correction

The actual mesh measurements, in the existing register coordinate system, are:

| Measurement | Result |
|---|---:|
| Physical slot width | 0.640625 units |
| Raised band width | approximately 0.4484375 units |
| Band / slot width | 70.0000% (mesh float tolerance) |
| Left / right mechanical margin | approximately 0.09609375 units each |
| Margin / slot width | 15.0000% each |
| Actual window clear height | approximately 0.7400000 units |
| Projected fitted OBB width / projected full-slot width | 69.6293%–70.6516% across five digits |
| Visible projected region / OBB area | 99.4815%–99.8675% |

Projected rectangle width does not have to equal exactly 70%: it is independently fitted after perspective projection and clipping, with the correct depth of the curved raised band. Every clipped projected surface vertex is enclosed. The minimal enclosing rectangle can contain a small amount of blank corner area under perspective, as required by the rectangular YOLO-OBB representation. Its fit never includes the whole mechanical side margin to force a fixed image-space ratio.

Visual inspection of the final green overlays confirms that the two axial edges follow the raised cream band, leave side pins outside, and retain the complete visible numeral-bearing region rather than tightly tracing the black glyph. The final `4` retains its original rolling pose and original frame clipping; no digit transition or geometry was changed.

## Projection implementation

`digitgen/band_annotations.py` supplies the new `project_numeral_bands` adapter for the approved raised-register scene. It:

1. Reads actual inner lip/separator mesh coordinates in register coordinates to recover each slot's width, height and two physical mask planes.
2. Reads the actual raised-band mesh dimensions; **no nominal 0.70 multiplier is used to generate labels**.
3. Obtains the evaluated mesh, including its existing bevel. Selects the printed outer material surface and rejects annular shoulder faces and back-facing facets. This selection is independent of atlas pixel values.
4. Transforms the surface vertices using the complete object world matrix and the active Blender camera. Projects each visible facet, clips it against both projected physical opening planes, and takes the convex hull of the remaining visible band.
5. Fits a minimum-area enclosing rectangle in **pixel space**, then normalizes its consistently clockwise corners to `[0,1]`. No image-space shrinking or rotation of a reference box is used.

The API reads current camera and register transforms on every call. It supports perspective yaw/pitch/roll and rigid register rotation, provided the assembly remains visible, with no new opaque occluders. It checks render resolution/aspect against the supplied pixel dimensions and refuses out-of-frame labels instead of clamping them. The five-digit reviewed model is the target; arbitrary heavily occluded new assemblies are not certified by this checkpoint.

The new single-sample entry point is `obb_band_stage1.py`, using `configs/obb_band_stage1.json`. Numeric class ID **0** and the existing nine-field YOLO-OBB format are retained; its descriptive class name is now `digit_band`. The legacy baseline `generate.py` still describes historical full-aperture datasets and is not the entry point for the upcoming approved-model Experiment 1. Stage 2 will use this band adapter after approval.

## Additional projection issue found

The earlier glass review computed front diagnostic labels while the scene retained the oblique camera's **1600 × 700** render aspect, then converted them to **1600 × 540** coordinates. Blender uses the scene aspect to determine framing, so those historical front diagnostic labels also had an undersized vertical span. This correction reads the actual window mesh and uses the real **1600 × 540** render state. A negative test now explicitly rejects mismatched aspect/resolution. Earlier delivery files are preserved; this batch supersedes those annotations for the approved model.

This is still an annotation correction: the camera, scene geometry, font atlas, lighting, native glass and shader values are unchanged. Scene fingerprints before/after include mesh coordinates/polygons/transforms, camera/light/world state, shader connections/default values and packed texture bytes. The adapter only reads evaluated geometry; it never edits modifiers. The render closely matches the prior neutral-glass RGB: maximum channel difference 1/255 and mean absolute channel difference approximately 0.00000424 in 8-bit channel units. No appearance editing is applied.

Glass remains a native physical layer. Exported labels are direct geometric band projections, not image-fitted refracted glyph boxes. The small optical shifts from the prior glass setup remain a limitation; the fixed front overlay has been visually inspected. New oblique images will require renewed optical alignment checks during Stage 2.

## Validation and reproducibility

- One RGB render, five labels, finite normalized coordinates in bounds, clockwise corners, rectangularity, boundary containment and label round-trip checks pass.
- All 20 existing host tests pass.
- The no-render Blender integration suite checks four independent perspective camera poses, yaw/pitch/roll, focal length/distance variation and register rotation. All yield five boxes, with 97.62%–98.19% minimum visible-region/OBB area per pose.
- An independent 0.1-degree orientation sweep finds no enclosing rectangle smaller than the computed minimum-area fit, and confirms fit tightness within 1%.
- Jointly transforming camera and register preserves projected boxes within **0.00034 px**, establishing that world transforms are honored.
- No-render recheck confirms the current implementation reproduces the five saved labels against the unchanged scene; it does not generate another RGB sample.

From the workspace, use a config with a new/empty `output` directory:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --python-exit-code 1 --python tests/band_projection_blender.py
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --python-exit-code 1 --python obb_band_stage1.py -- --config configs/obb_band_stage1.json
python3 review_band_stage1.py --output outputs/obb_band_stage1
```

Saved-sample verification without another render:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --python-exit-code 1 --python obb_band_stage1.py -- --recheck
```

The reviewed source is the saved neutral-glass scene from the previous batch: Blender 5.1.1, Cycles CPU, 64 samples, denoising, seed `20261029`, resolution 1600 × 540. Full source parameters and hashes are included. The frozen reproduction folder includes the input `.blend`, reference parameters, adapter, entry point, audit and tests.

**Checkpoint:** await approval of the green band OBBs before implementing or generating `diffusion_model_dataset/exp1`. No random dataset, FLUX/ComfyUI execution, font modification, transition-spacing adjustment or model training has occurred.
