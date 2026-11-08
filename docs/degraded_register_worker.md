# Heavily degraded register graphics worker

This worker uses the existing 3D register scene, digit atlas, wheel geometry, camera sampling, and glass scratches. It keeps the X-only image-space shear and refits the digit-strip OBBs after shear. The scene geometry is not removed: extrusion and fine mechanical detail become indistinct through simulated low-resolution imaging and blur.

The existing seeded glass scratch material is reused. Its scratch mask is broadened on the glass so some wear can survive downsampling; a seeded procedural glass-surface contamination shader adds dirty, irregular deposits, including deposits along the scratches. Images are rendered in Blender Cycles, downsampled to a simulated 240-pixel-wide sensor and restored to the original size, then processed with the existing 50% blur and sensor noise. The final X shear is applied to image and projected contours together. Fine scratches can still disappear at this blur level, and a heavy stain can reduce legibility. These examples have not been calibrated quantitatively against real photographs.

[Five-image comparison](../outputs/degraded_register_review_v3_20261107/contact_sheet.png). Unannotated images, YOLO OBB labels, per-image metadata, validation and Blender log are in the results folder. Label geometry does not account for optical refraction through glass. Overlay labels are geometric annotations and do not indicate whether individual digits remain readable.

From the repository root, reproduce with a new output directory:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python generate_degraded_register.py -- --count 5 --seed 2026110711 --output outputs/my_degraded_review
```

Adjust `--sensor-width` (60–1200; lower is coarser), `--blur-percent` (0–50), `--stain-strength` (0–1), `--scratch-count` (0–500), and `--scratch-width` (0–5 mask pixels); use `--no-shear` to disable shear. The review uses fixed values rather than a calibrated distribution. The worker depends on the existing source `.blend`, atlas, shaders and Python modules in this checkout; the included worker snapshot alone is not a standalone Blender project.
