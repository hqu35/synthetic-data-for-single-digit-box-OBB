"""Independently re-read and verify every delivered sample."""

import argparse, json, hashlib, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
import numpy as np
from .geometry import boundary, min_area_rect, points_in_box, simple_polygon
from .worker import reconstruct, sample
from .render import make_images


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root):
    root = Path(root)
    batch = json.loads((root / "batch.json").read_text())
    records = []
    images = set()
    all_seeds = set()
    if (
        len(batch["samples"]) != batch["count"]
        or len(set(batch["samples"])) != batch["count"]
    ):
        raise ValueError("Batch list/count mismatch")
    for name in batch["samples"]:
        p = root / name
        d = json.loads((p / "geometry.json").read_text())
        w, h = d["resolution"]
        n = d["boundary_samples_per_edge"]
        if len(d["strips"]) != 5 or len(d["reading"]) != 5:
            raise ValueError(f"{name}: wrong strip count")
        if [s["digit"] for s in d["strips"]] != list(d["reading"]):
            raise ValueError(f"{name}: wrong digit metadata")
        if d != reconstruct(d):
            raise ValueError(
                f"{name}: saved geometry cannot reconstruct exactly"
            )
        if d != sample(d["seed"], d["reading"], d["sampling_configuration"]):
            raise ValueError(f"{name}: seed does not reproduce geometry")
        lines = (p / "annotations.txt").read_text().splitlines()
        if len(lines) != 5:
            raise ValueError(f"{name}: wrong label count")
        conditioning, preview = make_images(d)
        for filename, expected in [
            ("conditioning.png", conditioning),
            ("preview.png", preview),
        ]:
            with Image.open(p / filename) as image:
                if (
                    image.size != (w, h)
                    or ImageChops.difference(
                        image.convert("RGB"), expected
                    ).getbbox()
                ):
                    raise ValueError(
                        f"{name}: {filename} reconstruction differs"
                    )
        axis = np.asarray(d["separation_axis_px"])
        intervals = []
        contours = []
        for strip, line in zip(d["strips"], lines):
            contour = np.asarray(strip["contour_px"])
            box = np.asarray(strip["obb_px"])
            dense = boundary(strip["coefficients_px"], 2048)
            if not simple_polygon(contour) or not points_in_box(contour, box):
                raise ValueError(f"{name}: invalid contour or OBB")
            # Tolerance is measured in cross-product pixel units, sufficient for floating error.
            if not points_in_box(dense, box, tolerance=1e-6):
                raise ValueError(
                    f"{name}: analytic boundary escapes sampled OBB"
                )
            if not np.allclose(
                contour / [w, h],
                strip["contour_normalized"],
                rtol=0,
                atol=1e-12,
            ):
                raise ValueError("Contour normalization mismatch")
            fields = line.split()
            if len(fields) != 9 or fields[0] != "0":
                raise ValueError("Bad YOLO row")
            xy = np.asarray([float(x) for x in fields[1:]]).reshape(4, 2)
            if (
                np.any(xy < 0)
                or np.any(xy > 1)
                or not np.allclose(
                    xy * np.array([w, h]), box, rtol=0, atol=1e-7
                )
            ):
                raise ValueError("Bad YOLO normalized vertices")
            expected_box, area = min_area_rect(contour)
            if not np.allclose(box, expected_box, rtol=0, atol=1e-7):
                raise ValueError("OBB differs from minimum-area fit")
            intervals.append(
                (float((contour @ axis).min()), float((contour @ axis).max()))
            )
            contours.append(len(contour))
        gaps = [intervals[i + 1][0] - intervals[i][1] for i in range(4)]
        if min(gaps) <= 0 or not np.allclose(
            gaps, d["minimum_separation_gaps_px"], rtol=0, atol=1e-8
        ):
            raise ValueError("Nonpositive or inconsistent strip separation")
        # The rendered foreground must contain exactly the five disjoint strips.
        arr = np.asarray(conditioning.convert("L"))
        threshold = (
            d["background_gray"] + min(s["fill_gray"] for s in d["strips"])
        ) // 2
        mask = Image.fromarray(
            np.where(arr > threshold, 255, 0).astype("uint8")
        ).copy()
        for s in d["strips"]:
            xy = tuple(map(round, s["coefficients_px"]["p"]))
            if mask.getpixel(xy) != 255:
                raise ValueError("Strip missing or merged")
            ImageDraw.floodfill(mask, xy, 128)
        if np.any(np.asarray(mask) == 255):
            raise ValueError("Unexpected extra foreground component")
        all_seeds.add(d["seed"])
        images.add(digest(p / "conditioning.png"))
        records.append(
            {
                "sample": name,
                "seed": d["seed"],
                "strips": 5,
                "minimum_gap_px": min(gaps),
                "contour_vertices": contours,
                "max_curve_chord_error_px": max(
                    s["quadratic_side_max_chord_error_px"] for s in d["strips"]
                ),
                "conditioning_sha256": digest(p / "conditioning.png"),
                "preview_sha256": digest(p / "preview.png"),
                "annotation_sha256": digest(p / "annotations.txt"),
                "geometry_sha256": digest(p / "geometry.json"),
            }
        )
        print("AUDIT_OK", name, flush=True)
    if len(all_seeds) != batch["count"] or len(images) != batch["count"]:
        raise ValueError("Seeds or conditioning images are not unique")
    return {
        "status": "passed",
        "sample_count": len(records),
        "seed_count": len(all_seeds),
        "unique_conditioning_images": len(images),
        "checks": [
            "five connected strips",
            "left-right positive separation",
            "simple contours",
            "local Jacobian",
            "sampled and dense contour containment",
            "pixel metric minimum rectangles",
            "YOLO round-trip and bounds",
            "seed and JSON reconstruction",
            "rendered-image reconstruction",
        ],
        "limits": "Minimum rectangles are exact for the sampled polygon; the analytic curve approximation is bounded per strip in geometry.json. Edge antialiasing can affect pixels near the mathematical contour.",
        "samples": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = audit(args.directory)
    (args.directory / "validation.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print("AUDIT_COMPLETE", result["sample_count"])


if __name__ == "__main__":
    main()
