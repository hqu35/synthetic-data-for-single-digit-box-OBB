"""Compare explicit X-shear coefficients on the same existing 3D image."""

# Load the single shared package without worker-local asset links.
import sys as _shared_sys
from pathlib import Path as _SharedPath

_shared_sys.path.insert(
    0,
    str(
        next(
            p / "shared"
            for p in _SharedPath(__file__).resolve().parents
            if (p / "shared" / "digitgen").is_dir()
        )
    ),
)
import copy, hashlib, json, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from digitgen.shear import apply_to_file
from digitgen.export import export_labels, write_json

ROOT = Path(__file__).resolve().parents[2]
src = ROOT / "outputs/scratch_multi_version"
out = ROOT / "outputs/x_shear_review_adaptive_2026-11-07"
if out.exists():
    raise ValueError("Use a new review output directory")
out.mkdir(parents=True)
for d in ("images", "previews", "labels", "metadata"):
    (out / d).mkdir()
original = src / "images/000005.png"
base = json.loads((src / "metadata/000005.json").read_text())
shutil.copy2(original, out / "original.png")
cases = [
    ("subtle_negative", -0.025),
    ("subtle_positive", 0.025),
    ("natural_negative", -0.07),
    ("natural_positive", 0.07),
    ("strong_negative", -0.115),
    ("strong_positive", 0.115),
]
for name, s in cases:
    image = out / "images" / f"{name}.png"
    shutil.copy2(original, image)
    regions, framing, affine = apply_to_file(
        image, base["regions"], base["framing"], s
    )
    label = out / "labels" / f"{name}.txt"
    export_labels(
        label, [r["obb_px"] for r in regions], affine["output_resolution"]
    )
    preview = Image.open(image).convert("RGB")
    draw = ImageDraw.Draw(preview)
    for i, r in enumerate(regions):
        pts = [tuple(x) for x in r["obb_px"]]
        draw.line(pts + [pts[0]], fill=(255, 183, 39), width=3)
        x, y = pts[0]
        draw.text(
            (x + 4, y + 3),
            str(i),
            fill="white",
            stroke_width=2,
            stroke_fill="black",
        )
    preview.save(out / "previews" / f"{name}.png")
    write_json(
        out / "metadata" / f"{name}.json",
        {
            "source_image": "outputs/scratch_multi_version/images/000005.png",
            "source_metadata": "outputs/scratch_multi_version/metadata/000005.json",
            "coefficient": s,
            "image_affine": affine,
            "framing": framing,
            "regions": regions,
            "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
            "label_sha256": hashlib.sha256(label.read_bytes()).hexdigest(),
        },
    )
    print("REVIEW_OK", name, flush=True)
font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 22)
board = Image.new("RGB", (1600, 3 * 320), "white")
draw = ImageDraw.Draw(board)
for i, (name, s) in enumerate(cases):
    im = Image.open(out / "previews" / f"{name}.png").convert("RGB")
    im.thumbnail((780, 270), Image.Resampling.LANCZOS)
    x = (i % 2) * 800
    y = (i // 2) * 320
    draw.text(
        (x + 10, y + 5),
        f"{name.replace('_', ' ')}   s = {s:+.3f}",
        fill="black",
        font=font,
    )
    board.paste(im, (x + (800 - im.width) // 2, y + 38))
board.save(out / "contact_sheet.png")
print("REVIEW_COMPLETE", flush=True)
