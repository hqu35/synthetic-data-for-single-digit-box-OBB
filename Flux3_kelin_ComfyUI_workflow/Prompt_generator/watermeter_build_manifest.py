#!/usr/bin/env python3
"""Build a pilot manifest from reference folders and native mask-worker samples."""
from __future__ import annotations
import argparse
import json
import random
from pathlib import Path
from watermeter_prompt_generator import (
    generate_configuration,
    make_prompt,
)
from watermeter_geometry import load_layout, yolo_obb_lines

EXTS = {".png", ".jpg", ".jpeg", ".webp"}
GROUPS = (
    ("clear", 34, 9, 0),
    ("noisy", 33, 0, 9),
    ("mixed", 33, 4, 5),
)


def images(folder):
    return sorted(
        str(p.resolve())
        for p in Path(folder).rglob("*")
        if p.is_file() and p.suffix.lower() in EXTS
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clear-dir", required=True)
    ap.add_argument("--noisy-dir", required=True)
    ap.add_argument(
        "--layouts-dir",
        required=True,
        help="Directory containing mask sample folders",
    )
    ap.add_argument("--out", default="pilot100.jsonl")
    ap.add_argument("--seed", type=int, default=539)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    clear, noisy = images(args.clear_dir), images(
        args.noisy_dir
    )
    if (
        len(clear) < 9
        or len(noisy) < 9
        or set(clear).intersection(noisy)
    ):
        raise ValueError(
            "Need 9+ disjoint clear and noisy reference images"
        )
    layouts = []
    layout_root = Path(args.layouts_dir)
    candidates = (
        [layout_root / 'geometry.json']
        if (layout_root / 'geometry.json').is_file()
        else sorted(layout_root.rglob('geometry.json'))
    )
    for geometry_file in candidates:
        geometry = load_layout(geometry_file.parent)
        layouts.append((geometry['mask_image'], geometry))
    layouts.sort(key=lambda x: x[0])
    if not layouts:
        raise ValueError(
            "No usable native mask sample folders"
        )
    # Paired layouts and digit configs across groups for comparison.
    shared = []
    for i in range(34):
        layout_path, geometry = rng.choice(layouts)
        config_seed = rng.randrange(2**32)
        diffusion_seed = rng.randrange(2**32)
        cfg = generate_configuration(
            geometry["digit_count"], config_seed
        )
        shared.append(
            (layout_path, geometry, diffusion_seed, cfg)
        )
    rows = []
    for group, n, c, z in GROUPS:
        for i in range(n):
            layout_path, geo, diffusion_seed, cfg = shared[
                i
            ]
            refs = rng.sample(clear, c) + rng.sample(
                noisy, z
            )
            rng.shuffle(refs)
            # Node index 0 controls latent/output size in ReferenceMultiLatent.
            # Keep geometry layout LAST as requested, but inspect output aspect ratios.
            flux_boxes = [
                w["flux_aabb_yxyx_1000"]
                for w in geo["windows"]
            ]
            sample_id = f"{group}_{i:03d}"
            rows.append(
                {
                    "id": sample_id,
                    "group": group,
                    "reference_images_ordered": refs
                    + [layout_path],
                    "reference_roles": ["appearance"] * 9
                    + ["layout"],
                    "layout_image": layout_path,
                    "layout_geometry": geo,
                    "yolo_obb_label_lines": yolo_obb_lines(
                        geo
                    ),
                    "prompt_config": cfg,
                    "prompt": make_prompt(cfg, flux_boxes),
                    "diffusion_seed": diffusion_seed,
                    "postprocess": {
                        "downscale_linear_factor": 0.7,
                        "upscale_to_original_dimensions": True,
                    },
                    "output_filename": sample_id + ".png",
                }
            )
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "\n".join(
            json.dumps(r, ensure_ascii=False) for r in rows
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(rows)} planned samples to {target}")


if __name__ == "__main__":
    main()
