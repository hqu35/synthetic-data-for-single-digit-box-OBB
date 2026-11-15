# Normalized AABB example

`sample_0001/conditioning.png` is the conditioning image and `sample_0001/preview.png` shows the sampled contours and exported AABBs. `aabb.json` contains four normalized coordinates per box. `annotations.txt` contains class 0 followed by the four coordinates. The original curved contours and diagnostic OBBs remain in `geometry.json`.

A frozen source snapshot and reproduction command are in `reproduction/`. Schema 2 uses AABB; existing schema 1 OBB datasets remain unchanged.
