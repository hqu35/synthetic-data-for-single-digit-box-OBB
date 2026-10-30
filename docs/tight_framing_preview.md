# Tight register framing — one-image preview

One new Blender image demonstrates the requested close framing: the register's projected outer silhouette occupies **93% of the image area**, leaving approximately **7% background**. The image is **1600 × 420 pixels**. The complete register and all five physical digit bands are inside the frame.

- [Clean preview](../outputs/tight_framing_preview/register_closeup.png)
- [Optional corrected-band OBB overlay](../outputs/tight_framing_preview/register_closeup_overlay.png)
- [Saved Blender scene](../outputs/tight_framing_preview/tight_framing_preview.blend)
- [Complete parameters and measured projected footprint](../outputs/tight_framing_preview/inspection_report.json)
- [Image and annotation validation](../outputs/tight_framing_preview/validation_report.json)
- [Configuration](../outputs/tight_framing_preview/config.json)
- [Frozen reproduction source and instructions](../outputs/tight_framing_preview/reproduction/README.md)

The camera focal length is fitted to the actual projected glass/seat mesh envelope. Coverage is measured as the area of that outer silhouette divided by the full image area; the register's viewing window and mechanical contents count as register. The fit is performed before rendering, without cropping or resizing a rendered environmental image.

The approved `00054` wheel states, mechanical geometry, raised bands, font atlas, glass shader and neutral illumination are preserved. Only camera framing and output aspect ratio change. This frontal preview uses zero camera roll to demonstrate the requested composition clearly. Existing digit transition behavior is unchanged.

Exactly one RGB image is rendered with Blender 5.1.1, Cycles CPU, 64 samples, denoising, six threads and seed `20261029`. Corrected numeral-band OBBs are recomputed for the new camera and saved separately; the clean RGB contains no annotations.

The 22 images from the rejected environmental framing remain preserved as superseded staging results. **The 100-image dataset batch remains paused.** This delivery is only the requested framing preview.

Reproduce from the source workspace, using a new/empty output directory in the config:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --python-exit-code 1 --python render_tight_framing_preview.py
python3 review_tight_framing_preview.py
```
