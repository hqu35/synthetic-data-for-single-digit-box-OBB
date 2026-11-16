# Reproduce the AABB sample

Requires Python, NumPy and Pillow. Run from this directory:

```sh
PYTHONPATH=. python3 -m geometry_worker generate --count 1 --seed 20261115 --reading 43882 --output aabb_sample
PYTHONPATH=. python3 -m geometry_worker.audit aabb_sample
```

The output directory must not exist. Boxes are in normalized `[xmin, ymin, xmax, ymax]` order, measured against the whole image. `aabb.json` has four numbers per box; `annotations.txt` prepends the class ID. The intended consumer's required schema has not been independently verified.
