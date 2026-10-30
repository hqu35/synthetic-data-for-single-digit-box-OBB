# Experiment 1 — 200 tightly framed register images

The requested dataset is complete: exactly **200 RGB images and 200 matching label files**, with **1,000 corrected numeral-band OBBs**. Every saved image was decoded and every label was validated. All 24 host tests passed. The renderer has stopped; no downstream inference or training was launched.

## Final measured results

| Check | Result |
|---|---|
| Accepted RGB images / matching labels | 200 / 200 |
| Digit-band OBBs | 1,000 (five per image) |
| Resolution | 1600 x 420 |
| Measured register coverage | 91.0466% to 93.9997% |
| Neutral / cool-blue images | 100 / 100 |
| RGB / pose / lighting uniqueness | 200 distinct images, 200 poses, 200 lighting settings |
| Sensor-noise-enabled images | 30 |
| Preflight rejected attempts | 46 |
| Failed render/camera-stage attempts | 0 |
| Maximum ideal glass displacement | 3.3586 px (1.8841% of band width) |
| Minimum visible-region / OBB area | 98.0425% |
| Maximum label export round-trip error | 8e-08 px |

The user requested a temporary stop and delivery of available files. When checked, the background renderer had already completed all 200 pairs and exited. This delivery contains those existing files; no additional rendering or downstream job was started.

## Scope

This controlled dataset isolates photographic appearance variation for a later human-reviewed image-to-image experiment. It preserves the approved mechanical register, stable Barlow Condensed Regular atlas, native glass, digit sequence `00054` and transition progress `[0, 0, 0, 0, 0.05]`. No FLUX inference, ComfyUI or training is launched.

Each accepted view must show the complete register with **90–95% projected register coverage** and approximately **5–10% background**. RGB resolution is **1600 × 420**. The outer glass/seat silhouette defines register coverage, including its viewing window and mechanical contents.

## Review artifacts

- [Dataset README](../diffusion_model_dataset/exp1/README.md)
- [Representative RGB contact sheet](../diffusion_model_dataset/exp1/previews/contact_sheet.png)
- [Matching OBB contact sheet](../diffusion_model_dataset/exp1/previews/overlay_contact_sheet.png)
- [All 200 images overview](../diffusion_model_dataset/exp1/previews/all_200_contact_sheet.png)
- [Validation report](../diffusion_model_dataset/exp1/validation_report.json)
- [Configuration](../diffusion_model_dataset/exp1/config.json)
- [Complete sample journal](../diffusion_model_dataset/exp1/metadata/samples.jsonl)
- [Image/label checksum manifest](../diffusion_model_dataset/exp1/dataset_manifest.sha256.json)
- [Frozen renderer and packed source scene](../diffusion_model_dataset/exp1/reproduction/README.md)

## Controlled variation

Camera yaw varies within ±8 degrees, pitch within ±4 degrees and distance within 16–19 scene units. The register independently rotates within ±2 degrees around X and ±3 degrees around Y/Z. Camera roll compensates the resulting long-axis image rotation and leaves a small requested final image-space roll within ±0.25 degrees. This preserves the wide, tightly filled composition: unrestricted large roll would introduce excessive background or crop the register.

The physical focal length and sensor shifts are solved per view for the sampled coverage target, 91–94%. Actual lens, camera matrix, field of view, sensor shift, register matrix, requested angles and resolved projected roll are stored. Focal length and distance are necessarily coupled by the occupancy constraint; the initial sampled lens is not misrepresented as the final fitted lens. No rendered image crop, resize or label-based framing is used.

Lighting is balanced between 100 neutral and 100 cool-blue presets. Real area-light positions, intensities and dimensions vary; the native broad/narrow reflected lights remain restrained. Temperature controls are recorded as Kelvin-inspired RGB tints, not claimed to be spectrally calibrated. Weak gradients and shadow softness arise from real light placement and size, rather than painted image effects.

Scene exposure varies from −0.20 to +0.15 EV. Plastic substrate colors vary mildly while ink, material topology, glass IOR 1.50 and glass roughness 0.035 remain unchanged. A separate camera stage applies a very mild contrast adjustment and optional weak seeded sensor noise. No geometric image transform or blur is applied.

## Annotation and image integrity

Each image has exactly five class-0 `digit_band` YOLO-OBBs. The adapter reads the actual central raised-band mesh and solid aperture boundaries, projects the visible evaluated surface after all transforms, clips it against both opening planes and fits a minimum-area pixel-space enclosing rectangle before normalization. The mesh band remains 70% of slot width with 15% physical margin on each side; the labels cover the cream numeral-bearing surface, not just black strokes.

Every pose is checked before rendering for framing, full register containment, band rectangle coverage/tightness, finite normalized coordinates and mechanical visibility rays. A rotated plane-parallel Snell diagnostic verifies that optical paths stay in the cover and ideal apparent displacement remains within the configured band-width tolerance. Labels remain original direct geometric projections; they are never silently refitted to refracted glyphs. Bevel/micro-normal effects are outside the ideal diagnostic and require the supplied visual overlay review.

Saved RGB is checked for band brightness, contrast and overexposure. The final audit decodes all images, rereads every exported label, verifies 1,000 band boundaries and rectangles, checks identity/transition metadata and file hashes, and generates representative, extreme-angle and all-image previews.

## Determinism and failed attempts

Seeds depend on the fixed base seed, sample index and bounded attempt number. Preflight geometries rejected for framing are logged, and the first valid deterministic attempt is reused during rendering. Any actual failed render or camera-stage attempt is logged separately and its files retained outside the final image/label directories. Final pair directories contain exactly the 200 accepted matching stems; failed attempts are never silently dropped.

The sample journal is appended after each successful image, label and per-sample JSON are saved. Resume verifies source-scene, renderer and artifact checksums and never re-renders a completed valid pair. Source reload per sample prevents accumulated material or transform changes.

## Reproduction

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --disable-autoexec --python-exit-code 1 --python generate_diffusion_exp1.py -- \
  --config configs/diffusion_exp1_200.json --plan-only
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --disable-autoexec --python-exit-code 1 --python generate_diffusion_exp1.py -- \
  --config configs/diffusion_exp1_200.json --resume
python3 validate_diffusion_exp1.py --output diffusion_model_dataset/exp1
```

Use a fresh output for full reproduction. The supplied frozen snapshot contains the source `.blend`, reference lighting parameters, config and renderer. Native rendering uses Blender 5.1.1, Cycles CPU, 32 samples, denoising and eight threads. Platform/version changes can alter rendered pixels. Do not execute regeneration simply to inspect the supplied dataset.

## Visual review

The representative RGB/OBB contact sheets and all five 40-image overview pages were inspected. The complete register stays in frame, the digit content remains readable, and the corrected green boxes exclude the mechanical side margins. The ideal-glass model limits stated above remain applicable.
