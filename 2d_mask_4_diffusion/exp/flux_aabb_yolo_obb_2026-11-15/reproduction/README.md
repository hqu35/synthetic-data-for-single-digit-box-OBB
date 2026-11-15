# Reproduce the dual-annotation sample

Requires Python, NumPy, and Pillow. From this directory:

```sh
PYTHONPATH=. python3 -m geometry_worker generate --count 1 --seed 20261115 --reading 43882 --output dual_sample
PYTHONPATH=. python3 -m geometry_worker.audit dual_sample
```

The output directory must not exist. `flux_bboxes.json` contains integer `[top,left,bottom,right]` values on 0–1000; `annotations.txt` preserves class 0 and four OBB corners normalized to 0–1. Boxes derive from the full image. The consumer's actual interface was not tested.
