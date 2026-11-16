# FLUX AABB and YOLO OBB annotations

Schema 3 keeps two separate representations from the same generated pixel-metric four-corner OBB. `annotations.txt` retains class 0 and the original four X/Y corners normalized to [0,1] by full image width and height. `flux_bboxes.json` contains integer `[top,left,bottom,right]` boxes in [0,1000], obtained by taking the min/max X and Y of those OBB corners and rounding the appropriately normalized values as requested. The output is validated for bounds and positive extent. Rounding can move an edge by at most half a 0–1000 unit.

[Sample FLUX boxes](../2d_mask_4_diffusion/exp/flux_aabb_yolo_obb_2026-11-15/sample_0001/flux_bboxes.json), [YOLO labels](../2d_mask_4_diffusion/exp/flux_aabb_yolo_obb_2026-11-15/sample_0001/annotations.txt), and [preview](../2d_mask_4_diffusion/exp/flux_aabb_yolo_obb_2026-11-15/sample_0001/preview.png). A frozen reproduction is included under `reproduction/`. The actual FLUX API and model were not tested.

Eight unit tests passed; one new sample passed its independent audit. The original 20 schema 1 samples and the interim schema 2 example passed compatibility audits without being rewritten. Same-seed OBB vertices and their 0–1 values were exactly identical to the original schema 1 sample. Reconstructing legacy geometry produces schema 3 without changing geometry. Geometry is exact for the sampled contour, subject to the recorded curve approximation and antialiasing limits.

This supersedes experiment 031, which was produced before the user clarified the required FLUX format and therefore uses an incompatible interim annotation format. It is retained as a historical delivery, not the recommended input.
