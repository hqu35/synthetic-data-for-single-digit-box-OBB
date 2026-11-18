"""Render rolling photographic atlas digits inside existing mask strips."""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "shared/assets/atlases"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mask-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--digits", required=True)
    parser.add_argument("--theta", type=float, required=True)
    args = parser.parse_args()
    if not 0 <= args.theta <= 1:
        parser.error("theta must be between 0 and 1")
    data = json.loads((args.mask_dir / "geometry.json").read_text())
    if len(args.digits) != len(data["strips"]) or not args.digits.isdigit():
        parser.error("Supply one digit per strip")
    metadata = json.loads((ASSETS / "current.json").read_text())
    atlas_path = ROOT / "shared" / metadata["path"]
    atlas = Image.open(atlas_path).convert("L")
    order = metadata["typography"]["tile_order"]
    tile_size = metadata["typography"]["segment_pixels"]
    source = Image.open(args.mask_dir / "conditioning.png").convert("RGB")
    image = np.asarray(source).copy()
    height, width = image.shape[:2]
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    for digit, strip in zip(args.digits, data["strips"]):
        c = strip["coefficients_px"]
        p, a, b, k = [np.asarray(c[key])
                      for key in ("p", "a", "b", "k")]
        dx, dy = xx - p[0], yy - p[1]
        det = a[0] * b[1] - a[1] * b[0]
        t = (a[0] * dy - a[1] * dx) / det
        for _ in range(4):
            cross = a[0] * k[1] - a[1] * k[0]
            residual = det * t + cross * t * t
            residual -= a[0] * dy - a[1] * dx
            t -= residual / (det + 2 * cross * t)
        rx = dx - b[0] * t - k[0] * t**2
        ry = dy - b[1] * t - k[1] * t**2
        s = (rx * a[0] + ry * a[1]) / a.dot(a)
        mask = (np.abs(s) <= 1) & (np.abs(t) <= 1)
        vertical = (t + 1) / 2 + args.theta
        offset = np.floor(vertical).astype(np.int32)
        fraction = vertical - offset
        ink = np.zeros((height, width), dtype=np.float32)
        for delta in (0, 1, 2):
            number = (int(digit) + delta - 1) % 10
            index = order.index(number)
            left = index * tile_size
            tile = atlas.crop((left, 0, left + tile_size, tile_size))
            tile = np.asarray(tile.transpose(Image.Transpose.TRANSVERSE))
            map_x = np.clip((s + 1) / 2, 0, 1)
            map_x = (map_x * (tile_size - 1)).astype(int)
            map_y = (fraction * (tile_size - 1)).astype(int)
            sampled = tile[map_y, map_x]
            ink = np.where(offset == delta - 1, sampled, ink)
        image[mask] = np.clip(155 - ink[mask] * 0.57, 0, 255)[:, None]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image).save(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
