"""Render nested window masks and center-strip annotations."""

import json
from pathlib import Path

from PIL import Image, ImageDraw


def make_images(data):
    width, height = data["resolution"]
    scale = 2
    size = (width * scale, height * scale)
    image = Image.new("L", size, data["background_gray"])
    draw = ImageDraw.Draw(image)
    for window, strip in zip(data["windows"], data["strips"]):
        outer = [(round(x * scale), round(y * scale))
                 for x, y in window["contour_px"]]
        inner = [(round(x * scale), round(y * scale))
                 for x, y in strip["contour_px"]]
        draw.polygon(outer, fill=data["window_gray"])
        draw.polygon(inner, fill=strip["fill_gray"])
    image = image.resize((width, height), Image.Resampling.LANCZOS)
    image = image.convert("RGB")
    preview = image.copy()
    draw = ImageDraw.Draw(preview)
    for strip in data["strips"]:
        box = [tuple(point) for point in strip["obb_px"]]
        draw.line(box + box[:1], fill=(255, 168, 25), width=2)
    return image, preview


def save_sample(data, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    image, preview = make_images(data)
    image.save(out / "conditioning.png")
    preview.save(out / "preview.png")
    rows = []
    for strip in data["strips"]:
        coords = [v for point in strip["obb_normalized"] for v in point]
        rows.append("0 " + " ".join(f"{v:.10f}" for v in coords))
    (out / "annotations.txt").write_text("\n".join(rows) + "\n")
    flux = {
        "coordinate_order": "top,left,bottom,right",
        "coordinate_range": [0, 1000],
        "normalized_to": "full_image",
        "box_definition": "full_continuous_strip_boundary_outward_rounded",
        "boxes": [strip["flux_bbox"] for strip in data["strips"]],
    }
    (out / "flux_bboxes.json").write_text(json.dumps(flux, indent=2) + "\n")
    (out / "geometry.json").write_text(json.dumps(data, indent=2) + "\n")
