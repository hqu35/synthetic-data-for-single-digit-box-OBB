# Protective glass review — Task B

Seven fixed `00054` Cycles inspection images are complete. The approved wheel assembly and stable Barlow Condensed atlas remain intact. This is an independent glass review; none of Task A's candidate fonts is substituted here. Stop for human review before dataset generation.

## Review entry points

- [Glass/no-glass, neutral, cool-blue and oblique comparison](../outputs/glass_review/glass_comparison.png)
- [Roughness 0.015 / 0.035 / 0.070](../outputs/glass_review/roughness_comparison.png)
- [Clean / subtle microstructure comparison](../outputs/glass_review/microstructure_comparison.png)
- [Front OBB inspection](../outputs/glass_review/02_glass_neutral_obb_inspection.png)
- [Oblique OBB inspection](../outputs/glass_review/04_glass_oblique_obb_inspection.png)
- [Packed native Blender scene](../outputs/glass_review/protective_glass_review.blend)
- [Complete inspection configuration and per-view metadata](../outputs/glass_review/inspection_report.json)
- [Saved-artifact audit and optical/image measurements](../outputs/glass_review/artifact_validation.json)
- [Frozen source, approved input scene, textures and reproduction instructions](../outputs/glass_review/reproduction/README.md)

Clean RGB files are separate from PNG/SVG overlays. Every numbered image has a corresponding `_parameters.json` and original `_slot_obbs.txt`. Green overlay lines represent those exported labels; thin orange lines show the ideal refracted-box diagnostic. Orange lines never replace the exported ground truth.

## Geometry and unit conversion

The existing scene uses arbitrary dimensions. **Assumption: the 0.74-unit clear aperture height represents 12 mm.** This configurable assumption is not a measurement of a real meter. It gives 0.0616667 Blender units/mm (16.2162 mm/unit). Physical target dimensions are converted using that factor:

| Parameter | Target | Scene value |
|---|---:|---:|
| Glass thickness | 1.5 mm | 0.0925 |
| Air gap from highest mechanical collar surface | 4 mm | 0.2466667 |
| Side / vertical margins | 1.5 mm | 0.0925 each |
| Whole cover width / height | derived | 3.695625 / 0.925 |
| Back / front surface Z | derived | 1.5116667 / 1.6041667 |

One continuous closed solid covers all five apertures. A three-segment bevel is 3% of thickness. Evaluated mesh checks establish manifold closure and positive signed volume; the cover is parented to the new identity-transform `RegisterHousing` with the approved assembly. Narrow external seat strips lie outside the clear cover. The panes are not split by digit. There is a positive gap to the entire rotating wheel/pin envelope and no glass coplanar with the old front mask.

The renderer compares hashes of wheel and axle mesh coordinates, polygon indices, world transforms and bevel settings before and after adding glass and before every render. These checks pass. Wheel radii, raised band, side pins, slot pitch, roll state and stable atlas remain unchanged. The existing source scene is preserved.

## Native optical material and illumination

Blender 5.1.1 Principled BSDF uses white base color, metallic 0, **Transmission Weight 1**, IOR 1.50, roughness 0.035, Alpha 1 and Specular IOR Level 0.5. Normal-incidence Fresnel reflection is 4% per air/glass interface. Cycles handles transmission and both physical interfaces. Alpha is never reduced to fake transparency.

The unchanged mechanical fill rig is supplemented with two real rectangular area lights: a broad soft reflection (energy 6, size 1.6 × 0.3) and a narrow highlight (energy 1.5, size 0.8 × 0.035). Position, target/orientation, energy, color and dimensions are configurable in `configs/glass_review.json`; actual resolved lights are recorded per image. Their highlights sit primarily near the upper border and move with the oblique camera. No painted streak, composited reflection, glare/bloom pass or opacity overlay is used. The cool variant changes light colors only. Baseline and neutral use exactly equal camera and light records; baseline hides only the cover and retains the same surrounding seat.

Microstructure is independently toggleable. Object-coordinate 3D noise (scale 85, detail 2) perturbs roughness within ±0.004 and drives a bump node at strength 0.003, distance 0.0005 units. It does not displace mesh geometry. The separate optional image sensor stage has linear-RGB noise standard deviation 0.0005 and a fixed seed; it is **disabled in all seven review images**. Procedural material noise, Cycles sampling noise and sensor noise remain separate controls. The microstructure comparison is intentionally very subtle.

## Optical and OBB validation

Each original physical slot is evaluated through an ideal parallel glass slab using Snell's law, with 96 sampled boundary points on each of the front/back aperture planes. The solver checks that both glass intersections remain inside the same finite cover. Original projected slot OBBs remain the exported labels.

| Diagnostic | Measured maximum | Review threshold |
|---|---:|---:|
| Front ideal boundary displacement | 1.4894 px | 2 px |
| Oblique ideal boundary displacement | 4.4274 px | — |
| Oblique displacement / projected slot width | 2.1100% | 2.5% |

An independent rendered-image cross-check matches gradients inside each front slot between no-glass and neutral glass. Best integer translations are `[-1,0], [-1,0], [0,0], [0,0], [1,0]` px, with correlation 0.895–0.973. This supports a small apparent shift; it does not estimate exact subpixel ground truth. The saved-label round-trip error is below 0.000001 px, and every image has five finite, in-bounds original labels. Visual inspection of the final front and oblique overlays shows the slight offset expected from refraction, with no severe digit clipping or warping introduced by this cover.

**Limits:** the analytic model assumes a flat, parallel, world-Z slab and excludes the bevel and perturbed micro-normals. The rendered oblique overlay visibly retains a few pixels of mismatch; labels are not claimed to be optically exact. The thresholds are declared inspection tolerances for these fixed views, not certification for arbitrary future poses or production datasets. More oblique poses require revalidation. No ground truth is silently fitted to the glass image.

No-render Blender optics invariants pass: central normal incidence for IOR 1/1.33/1.5/2, IOR-1 agreement with nine direct perspective projections, expected displacement direction and rejection of a finite-cover miss. [Test log](../outputs/glass_review/optics_invariants.log). All 20 existing host tests pass. These checks complement the seven actual native renders and visual inspection.

## Reproduce

From the source workspace, choose a new/empty output directory:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --python-exit-code 1 --python glass_review.py -- --output outputs/glass_review_new
python3 review_glass.py --output outputs/glass_review_new
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --python-exit-code 1 --python tests/optics_invariants_blender.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

All review renders use Cycles CPU, 64 samples, denoising, 6 threads and seed `20261029`. Platform/Blender changes may change pixels. The delivered reproduction folder freezes the implementation, helper modules, stable source `.blend`, reference report and assets; its config changes only the two source paths to its included copies.

**Deferred:** atlas blank spacing, 36° pitch/transition calibration and rolling-transition midpoint are unchanged. No diffusion, randomized dataset, training or production batch has been started.
