#!/usr/bin/env python3
"""Generate one 2D mask and its immediately matched water-meter prompt."""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASK_ROOT = ROOT / "2D_Mask_for_Diffusion"
from watermeter_geometry import load_layout, yolo_obb_lines
from watermeter_prompt_generator import (
    generate_configuration,
    make_prompt,
    SCENARIOS,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="New output directory"
    )
    parser.add_argument("--mask-seed", type=int, default=20261115)
    parser.add_argument("--prompt-seed", type=int, default=539)
    parser.add_argument("--scenario", choices=SCENARIOS)
    parser.add_argument("--mask-config", type=Path)
    parser.add_argument("--mask-version", choices=("v1", "v2"), default="v2")
    parser.add_argument("--windows", type=int, choices=(5, 6))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output path already exists")
    version_dir = MASK_ROOT / f"2d_mask_4_diffusion_{args.mask_version.upper()}"
    sys.path.insert(0, str(version_dir))
    if args.mask_version == "v2":
        from mask_v2.worker import DEFAULT_CONFIG, sample
        from mask_v2.render import save_sample
    else:
        from geometry_worker.worker import DEFAULT_CONFIG, sample
        from geometry_worker.render import save_sample
        if args.windows not in (None, 5):
            parser.error("V1 supports exactly five windows")
    cfg = json.loads((args.mask_config or DEFAULT_CONFIG).read_text())
    if args.mask_version == "v2" and args.windows is not None:
        cfg["window_count"] = args.windows
    args.output.mkdir(parents=True)
    sample_dir = args.output / "mask"
    data = sample(args.mask_seed, cfg)
    save_sample(data, sample_dir)
    layout = load_layout(sample_dir)
    prompt_config = generate_configuration(
        layout["digit_count"], args.prompt_seed, args.scenario
    )
    boxes = [window["flux_aabb_yxyx_1000"] for window in layout["windows"]]
    prompt = make_prompt(prompt_config, boxes, layout["mask_version"])
    layout["mask_image"] = (
        "mask/conditioning.png"  # Relative to layout_prompt.json for portability.
    )
    (args.output / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
    (args.output / "prompt_config.json").write_text(
        json.dumps(prompt_config, indent=2) + "\n"
    )
    (args.output / "layout_prompt.json").write_text(
        json.dumps(
            {
                "layout": layout,
                "prompt_config": prompt_config,
                "prompt": prompt,
                "yolo_obb_label_lines": yolo_obb_lines(layout),
                "guidance_note": "Bounding boxes are prompt-text guidance; no box-aware runtime is invoked.",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    print(f"Created {layout['digit_count']} aligned windows in {args.output}")


if __name__ == "__main__":
    main()
