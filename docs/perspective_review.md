# Moderate perspective review — five annotated images

Five fixed `00054` views demonstrate visibly stronger, physically projected 3D perspective. Each view has five green oriented bounding boxes around the actual numeral-bearing bands. The camera produces the perspective directly in Blender; no 2D shear, image warp or rectangle-to-parallelogram filter is applied.

## Requested annotated images

| View | Camera yaw / pitch | Annotated image | YOLO-OBB labels | Clean RGB | Complete parameters |
|---|---:|---|---|---|---|
| 1 | −14° / −3° | [OBBs](../outputs/perspective_review/overlays/000001.png) | [Labels](../outputs/perspective_review/labels/000001.txt) | [RGB](../outputs/perspective_review/images/000001.png) | [JSON](../outputs/perspective_review/metadata/000001.json) |
| 2 | −14° / +3° | [OBBs](../outputs/perspective_review/overlays/000002.png) | [Labels](../outputs/perspective_review/labels/000002.txt) | [RGB](../outputs/perspective_review/images/000002.png) | [JSON](../outputs/perspective_review/metadata/000002.json) |
| 3 | +14° / −3° | [OBBs](../outputs/perspective_review/overlays/000003.png) | [Labels](../outputs/perspective_review/labels/000003.txt) | [RGB](../outputs/perspective_review/images/000003.png) | [JSON](../outputs/perspective_review/metadata/000003.json) |
| 4 | +14° / +3° | [OBBs](../outputs/perspective_review/overlays/000004.png) | [Labels](../outputs/perspective_review/labels/000004.txt) | [RGB](../outputs/perspective_review/images/000004.png) | [JSON](../outputs/perspective_review/metadata/000004.json) |
| 5 | +15° / 0° | [OBBs](../outputs/perspective_review/overlays/000005.png) | [Labels](../outputs/perspective_review/labels/000005.txt) | [RGB](../outputs/perspective_review/images/000005.png) | [JSON](../outputs/perspective_review/metadata/000005.json) |

- [All five OBB overlays together](../outputs/perspective_review/previews/overlay_contact_sheet.png)
- [Clean RGB comparison](../outputs/perspective_review/previews/contact_sheet.png)
- [Image/label/geometry validation](../outputs/perspective_review/validation_report.json)
- [Measured comparison with the previous 200 views](../outputs/perspective_review/perspective_comparison.json)
- [Frozen implementation, source scene and reproduction](../outputs/perspective_review/reproduction/README.md)

The `overlays/` folder contains the five requested images. The separate clean RGB images are the same five renders without drawn labels; they are not additional rendered samples. Each overlay is drawn from the corresponding saved YOLO-OBB text file.

## What changed

The previous worker had a perspective camera, but its long camera distance of 16–19 scene units and fitted focal lengths of about 144–174 mm produced nearly parallel register edges. The worker now provides a **measured perspective mode**, enabled in [the review configuration](../outputs/perspective_review/config.json), and rejects configurations without that check by default. Historical near-frontal configurations require an explicit `--allow-legacy-framing` flag; their previously delivered frozen reproduction snapshot is unchanged.

The new fixed review poses use camera distances 7.5–8 scene units, fitted focal lengths 70.06–74.98 mm, yaw −14° to +15°, and pitch −3° to +3°. The register is viewed from both the left and the right. The active camera is Blender's `PERSP` camera, and the four actual 3D glass-front corners are projected independently through its perspective matrix. Their projected quadrilateral may be a trapezoid or another perspective quadrilateral; it need not be a mathematically exact parallelogram.

The perspective measurement is the absolute difference between the projected left and right glass-edge heights divided by their average. Applying the same 3D-corner measurement to the saved camera metadata of the previous 200 images gives **1.33% mean, 3.53% maximum**. The five new images measure **12.44%–12.49%**. Those measurements come from the physical scene and camera, with no extra renders. [Full comparison](../outputs/perspective_review/perspective_comparison.json).

Each 1600 × 460 image contains the complete register, occupying approximately **90.50%** of the image area, leaving about **9.50%** background. Camera fitting is performed before rendering from the actual projected glass/seat silhouette. A small image aspect-ratio adjustment from the previous 1600 × 420 framing keeps the complete perspective quadrilateral within the requested close view.

The existing geometry, `00054` wheel states, font atlas, native glass, OBB class ID and band dimensions are preserved. Lighting remains varied and restrained: three neutral and two cool-blue views. No digit-spacing recalibration or new dataset has been generated.

## OBB validation and optical limit

Each image has **five** class-0 YOLO-OBB labels, for 25 total. The worker transforms the actual raised-band 3D mesh, clips visible facets against the physical opening, projects with the active camera and fits a minimum-area enclosing rotated rectangle in pixel coordinates. The boxes cover the cream numeral-bearing band, not only black strokes; side pins and the mechanical margins remain outside the target region. Full 3D projected boundaries, camera matrices, lights, random seeds, label coordinates and image hashes are recorded for every view.

All five PNGs decode successfully, all 25 rectangles are finite, normalized, correctly ordered, within the image, and enclose the projected visible-band boundaries. Their visible-region-to-OBB area ratio is at least **96.88%**. The saved-label round-trip error is below 0.000001 pixel. Three rays per band confirm that the corresponding numeral-band surface is visible.

**Glass refraction is a real limit on apparent alignment.** The ideal parallel-slab diagnostic estimates a maximum displacement of **6.06 pixels**, or **3.50% of the band width**, just within the configured 3.5% review threshold. The exported labels remain direct projections of the physical band; they have not been silently fitted to visible glyphs. The model excludes bevel and micro-normal effects, so the overlays are supplied for visual review and this result is not an all-pose certification.

The five preflight poses passed without a retry. All 25 host tests passed, the rendered images and overlays were visually inspected, and no render attempt failed. The implementation and source scene are included in the reproduction folder; the saved renderer hash matches the one recorded in every sample.

## Reproduce

From the workspace, with a new/empty configured output directory:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --disable-autoexec --python-exit-code 1 --python generate_diffusion_exp1.py -- \
  --config configs/perspective_review.json --plan-only
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --disable-autoexec --python-exit-code 1 --python generate_diffusion_exp1.py -- \
  --config configs/perspective_review.json --resume
python3 validate_diffusion_exp1.py --output outputs/perspective_review
```

The preflight renders zero images; the render pass generates exactly five. Rendering uses Blender 5.1.1, Cycles CPU, 32 samples, denoising and eight threads. Complete per-image seeds and resolved settings are saved. Different platforms or Blender versions may change pixels slightly.
