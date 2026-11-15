# Normalized AABB geometry worker

The statistical geometry worker now exports the smallest axis-aligned box enclosing each sampled digit-strip contour. Each box is `[xmin, ymin, xmax, ymax]`: x coordinates are divided by full image width, y coordinates by full image height. Pixel-edge coordinates start at the top left, with x rightward and y downward. Schema 2 outputs `aabb.json` with five four-number arrays and `annotations.txt` with class `0` followed by four numbers on each row. The exact FLUX input schema and coordinate order were not independently verified.

The curved strip geometry and diagnostic minimum-area OBB remain in `geometry.json`. Bounding boxes enclose the sampled polygon; the continuous curve may deviate from it by the recorded per-strip chord-error bound, and antialiased raster pixels near the boundary may differ. Image crops or padding after generation require box recomputation.

[Example preview](../2d_mask_4_diffusion/exp/aabb_review_2026-11-15/sample_0001/preview.png), [four-coordinate JSON](../2d_mask_4_diffusion/exp/aabb_review_2026-11-15/sample_0001/aabb.json), and [class-prefixed labels](../2d_mask_4_diffusion/exp/aabb_review_2026-11-15/sample_0001/annotations.txt). A frozen reproduction is under `reproduction/` in the results.

One new example was generated and independently audited; seven unit tests passed, including reconstruction and tightness against contour extrema. Twenty existing schema 1 OBB samples were independently audited read-only. Existing datasets were not rewritten; reconstructing a schema 1 sample now produces a schema 2 AABB sample with the same geometry. The frozen reproduction matched all five sample artifacts byte-for-byte. No model inference was run.
