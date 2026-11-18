"""Draw the five prompt rectangles as a deterministic plot on the original image."""

from pathlib import Path
import hashlib, json, shutil
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image

out = Path(__file__).resolve().parent
source = (
    out / "original.png"
    if (out / "original.png").exists()
    else Path("/Users/ququ/Downloads/create-a-realistic.png")
)
with Image.open(source) as img:
    image = img.convert("RGB")
    width, height = image.size
if source.resolve() != (out / "original.png").resolve():
    shutil.copy2(source, out / "original.png")
boxes = [
    ("0", [250, 105, 755, 235]),
    ("3", [250, 265, 755, 395]),
    ("7", [250, 425, 755, 555]),
    ("8", [250, 585, 755, 715]),
    ("4", [250, 745, 755, 875]),
]
colors = ["#ffe138", "#34e8ff", "#ff6184", "#79ef72", "#ed8cff"]
rows = []
for digit, (top, left, bottom, right) in boxes:
    rows.append(
        {
            "digit": digit,
            "normalized_tlbr": [top, left, bottom, right],
            "pixel_xyxy": [
                left * width / 1000,
                top * height / 1000,
                right * width / 1000,
                bottom * height / 1000,
            ],
        }
    )


def show(ax, annotated):
    ax.imshow(image, extent=(0, width, height, 0), interpolation="nearest")
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.axis("off")
    if annotated:
        for row, color in zip(rows, colors):
            x0, y0, x1, y1 = row["pixel_xyxy"]
            ax.add_patch(
                Rectangle(
                    (x0, y0),
                    x1 - x0,
                    y1 - y0,
                    linewidth=2.2,
                    edgecolor=color,
                    facecolor="none",
                )
            )
            ax.text(
                x0 + 3,
                y0 + 4,
                row["digit"],
                ha="left",
                va="top",
                color="#101820",
                fontsize=12,
                fontweight="bold",
                bbox={"facecolor": color, "edgecolor": "none", "pad": 2},
            )


fig = plt.figure(figsize=(width / 100, height / 100), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
show(ax, True)
fig.savefig(out / "prompt_boxes_overlay.png", dpi=100)
plt.close(fig)
fig = plt.figure(figsize=(11.68, 10.8), dpi=100, facecolor="white")
a = fig.add_axes([0, 0.525, 1, 0.4593])
b = fig.add_axes([0, 0.025, 1, 0.4593])
show(a, False)
show(b, True)
fig.text(
    0.01,
    0.995,
    "Original image",
    ha="left",
    va="top",
    fontsize=13,
    fontweight="bold",
)
fig.text(
    0.01,
    0.495,
    "Prompt boxes [top, left, bottom, right]",
    ha="left",
    va="top",
    fontsize=13,
    fontweight="bold",
)
fig.savefig(out / "comparison.png", dpi=100)
plt.close(fig)
(out / "coordinates.json").write_text(
    json.dumps(
        {
            "source_name": source.name,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "image_size": [width, height],
            "normalization": "[top,left,bottom,right] on 0–1000 grid",
            "boxes": rows,
            "scope": "Prompt boxes only; no independently annotated ground-truth boxes, so IoU is not calculated.",
        },
        indent=2,
    )
    + "\n"
)
print("Created comparison and overlay at", out, "source size", width, height)
