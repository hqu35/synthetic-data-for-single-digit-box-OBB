# Statistical geometry worker — review

[Conditioning overview](../outputs/statistical_geometry_001/conditioning_contact_sheet.png) · [Contour/OBB overview](../outputs/statistical_geometry_001/contact_sheet.png) · [All samples](../outputs/statistical_geometry_001/) · [Per-sample validation](../outputs/statistical_geometry_001/validation.json) · [Frozen reproduction package](../outputs/statistical_geometry_001/reproduction/README.md)

The independent `geometry_worker` module generates five grayscale strip regions with mild curvature and correlated pose variation. It has no Blender or diffusion dependency. The reading `43882` is stored as metadata, not drawn. Each sample provides an unannotated conditioning PNG, an annotated preview, five normalized class-0 YOLO-OBB rows, and a JSON file containing the sampled parameters, pixel and normalized contours, and OBBs.

## Architecture and mapping

- `geometry_worker/worker.py`: seeded bounded sampling, one shared homography, correlated local coefficients and deterministic reconstruction.
- `geometry_worker/geometry.py`: quadratic boundary sampling, polygon validation, convex hull and pixel-space minimum-area rectangle.
- `geometry_worker/render.py`: neutral conditioning image and separate diagnostic preview/contact sheets.
- `geometry_worker/audit.py`: reopens each sample and verifies rendering, geometry, labels and reconstruction.
- `geometry_worker/config.json`: configurable provisional ranges and image dimensions.

For each strip, pixel coordinates are `F(s,t) = p + a*s + b*t + k*t²`, where `s,t ∈ [-1,1]`. Centers are positioned with a shared homography, and local directions use its Jacobian. This is a local quadratic approximation with coherent projective variation; it does not claim exact perspective projection of a curved 3D surface. A sampled, closed boundary polygon drives both the fill and its minimum-area bounding rectangle. Rectangles are computed in pixel space before x/y normalization.

## Provisional ranges

No statistically calibrated real digit-strip annotations were identified: the available Phase I ground truth labels entire registers and the Phase II detections are not independently verified digit-strip ground truth. The following default ranges are explicitly provisional:

| Parameter | Range |
|---|---|
| Strip width / image width | 0.138–0.155 |
| Strip height / image height | 0.64–0.76 |
| Nominal gap / strip width | 0.15–0.27 |
| Shared image roll | −2.5° to +2.5° |
| Horizontal / vertical perspective coefficient | −0.13 to 0.13 / −0.025 to 0.025 |
| Horizontal / vertical scale | 0.96–1.02 / 0.97–1.02 |
| Shared slant / curvature | ±0.07 / ±0.11 strip half-width |
| Local width / height variation | ±1.2% |
| Local curvature variation | ±0.015 strip half-width |

The final projected gaps vary with curvature, slant and the shared transformation. Invalid samples are rejected. The delivered 20 images have distinct seeds and conditioning-image hashes; their minimum projected separating gap is 11.11 pixels.

## Validation and limitations

All 20 samples passed the audit for five connected non-overlapping strips, left-to-right separation, simple sampled contours, nonzero Jacobians, sampled and densely sampled continuous-boundary OBB containment, minimum-area fits, normalized coordinates, image bounds, seed reproducibility, and reconstruction of the image and labels. Six host unit tests passed. The frozen reproduction package independently regenerated the first sample's JSON, labels, conditioning PNG and preview PNG byte-for-byte in the tested environment.

The minimum-area rectangle is exact for the sampled boundary polygon, not a symbolic minimum for the continuous quadratic. The maximum computed side-to-chord approximation bound in this batch is under 0.00062 pixels; dense numerical checks are not a formal proof of continuous-boundary containment. Raster antialiasing can affect pixels near the mathematical region boundary. No real-image distribution accuracy or downstream model performance has been measured.
