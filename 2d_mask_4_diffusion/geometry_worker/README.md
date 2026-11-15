# Statistical digit-strip geometry worker

A standalone, NumPy-and-Pillow worker for generating five simple curved strip regions and matching normalized axis-aligned bounding boxes. It does not import Blender, render numerals, or generate photorealistic content. The reading is stored as metadata only. This module is independent of the existing 3D Graphics Worker.

## Usage

From the repository root, choose an output directory that does not yet exist:

```bash
PYTHONPATH=2d_mask_4_diffusion python3 -m geometry_worker generate --count 20 --seed 20261104 --reading 43882 --output 2d_mask_4_diffusion/exp/my_geometry_batch
PYTHONPATH=2d_mask_4_diffusion python3 -m geometry_worker.audit 2d_mask_4_diffusion/exp/my_geometry_batch
```

For an arbitrary five-ASCII-digit reading, replace `--reading 43882`. Edit a copy of `2d_mask_4_diffusion/geometry_worker/config.json` and pass `--config path/to/config.json` to alter ranges or image dimensions. To rebuild a sample directly from its saved coefficients:

```bash
PYTHONPATH=2d_mask_4_diffusion python3 -m geometry_worker reconstruct --input 2d_mask_4_diffusion/exp/my_geometry_batch/sample_0001/geometry.json --output /private/tmp/my_geometry_reconstructed
```

Each sample contains a clean `conditioning.png`, a separate `preview.png`, normalized `annotations.txt`, `aabb.json`, and `geometry.json`. The batch also includes contact sheets for conditioning images and diagnostic previews. Preview colors: green sampled contour, orange AABB, red AABB corners; numbers identify strip positions 0–4 rather than digit classes. Each new annotation line is class `0` followed by `xmin ymin xmax ymax`, normalized by the full image width and height. `aabb.json` stores each four-value box without the class prefix. Dimensions are 1200 × 460 by default.

## Geometry

For each strip, in pixel coordinates, `F(s,t) = p + a*s + b*t + k*t²`, with `s,t` in `[-1,1]`. A shared sampled homography places the strip centers; its Jacobian determines their local horizontal and vertical bases. A small shared slant and curvature plus small local perturbations create coherent strip geometry. This is a local quadratic approximation to projective geometry, not a fully projective curved surface or a calibrated physical camera. Coefficients, homography, random seed, sampled values and the complete configuration are saved in each `geometry.json`.

The renderer uses exactly the same sampled boundary polygon that is stored as the contour and fitted by the OBB. Each contour has 128 points per edge by default. The output AABB is the min/max extent of the sampled contour in pixel space before normalization. The pixel-metric minimum-area OBB remains in metadata for diagnostics. The maximum analytic quadratic-to-chord deviation for a side is bounded by `||k|| / N²` pixels and recorded per strip. Raster antialiasing may color pixels close to the continuous contour outside its mathematical boundary; the annotations describe the geometry rather than a thresholded raster mask.

## Sampling ranges

These values are **provisional and not statistically calibrated**. Available Phase I labels describe whole registers; available Phase II detections are not independent digit-strip ground truth. No empirical parameter distribution is claimed.

| Parameter | Default range |
|---|---|
| Strip width / image width | 0.138–0.155 |
| Strip height / image height | 0.64–0.76 |
| Gap / strip width | 0.15–0.27 |
| Shared image roll | −2.5° to +2.5° |
| Horizontal / vertical perspective coefficient | −0.13 to 0.13 / −0.025 to 0.025 |
| Horizontal foreshortening / vertical scale | 0.96–1.02 / 0.97–1.02 |
| Shared slant / curvature | −0.07 to 0.07 / −0.11 to 0.11, in units of strip half-width |
| Local width / height perturbation | ±1.2% |
| Local curvature perturbation | ±0.015 strip half-width |

All parameters use bounded uniform sampling and are stored. The shared transform and shared slant/curvature correlate adjacent strips. Invalid, overlapping, folded, non-simple, out-of-frame, or degenerate configurations are rejected, up to the configured attempt limit.

## Validation

```bash
PYTHONPATH=shared:2d_mask_4_diffusion:3D_worker python3 -m unittest tests.test_statistical_geometry_worker
PYTHONPATH=2d_mask_4_diffusion python3 -m geometry_worker.audit 2d_mask_4_diffusion/exp/my_geometry_batch
```

The audit reloads every JSON and recomputes polygons, minimum rectangles, AABB labels, seeded samples, and images. It verifies five connected foreground strips, ordered nonoverlapping regions, Jacobian and polygon validity, boundary containment, normalization, and image bounds. It also tests a dense sample of the continuous quadratic edges. The analytic edge test is a dense numerical check, not a symbolic proof that the sampled-polygon OBB encloses every real-valued parameter point.

## Compatibility

Version 2 samples export `aabb.json` and five class-prefixed AABB rows. Version 1 samples retain their original OBB annotations and can still be audited. Reconstructing a version 1 geometry file creates a version 2 sample with unchanged contours and AABB annotations. Coordinate convention is pixel-edge origin at top left, x increasing right and y increasing down. If the image is cropped or padded later, recompute boxes against the resulting canvas.
