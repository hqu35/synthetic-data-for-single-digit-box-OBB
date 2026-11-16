"""Load mask-worker geometry for prompt generation."""

from __future__ import annotations
import json
from pathlib import Path


def load_layout(folder: str | Path) -> dict:
    folder = Path(folder).resolve()
    image_path = folder / 'conditioning.png'
    if not image_path.is_file():
        raise FileNotFoundError(image_path)
    data = json.loads(
        (folder / 'geometry.json').read_text()
    )
    strips = data['strips']
    return {
        'digit_count': len(strips),
        'resolution': data['resolution'],
        'mask_seed': data['seed'],
        'mask_image': str(image_path),
        'windows': [
            {
                'slot': i + 1,
                'flux_aabb_yxyx_1000': strip['flux_bbox'],
                'yolo_obb_xy_01': strip['obb_normalized'],
            }
            for i, strip in enumerate(strips)
        ],
    }


def yolo_obb_lines(layout: dict) -> list[str]:
    return [
        '0 '
        + ' '.join(
            f'{v:.10f}'
            for point in w['yolo_obb_xy_01']
            for v in point
        )
        for w in layout['windows']
    ]
