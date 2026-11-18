"""Reproducible image-space X shear and geometry-derived OBBs.

Coordinates are pixel-edge coordinates, x right/y down. The affine map is
x_out=x+s*(y-h/2)+pad, y_out=y. Padding protects the register and boxes.
"""

import copy, math, random
import numpy as np
from .geometry import minimum_rectangle, area

# Categories overlap by design: these are ranges conditional on the sampled
# bucket, not mutually exclusive magnitude bands.
SHEAR_BUCKETS = (
    ("subtle", 0.50, 0.03),
    ("natural", 0.30, 0.08),
    ("strong", 0.20, 0.12),
)


def make_shear_plan(seeds, enabled=True):
    """Stratified random categories and independent per-image coefficients."""
    seeds = list(seeds)
    if not seeds:
        return []
    if not enabled:
        return [{"bucket": "disabled", "s": 0.0} for _ in seeds]
    rng = random.Random((int(seeds[0]) ^ 0x53484541) + len(seeds))
    uniforms = [(i + rng.random()) / len(seeds) for i in range(len(seeds))]
    rng.shuffle(uniforms)
    result = []
    for seed, u in zip(seeds, uniforms):
        bucket, bound = (
            ("subtle", 0.03)
            if u < 0.5
            else (("natural", 0.08) if u < 0.8 else ("strong", 0.12))
        )
        s = random.Random(int(seed) ^ 0x58534852).uniform(-bound, bound)
        result.append({"bucket": bucket, "s": s, "range": [-bound, bound]})
    return result


def affine_for_shape(width, height, s):
    s = float(s)
    if not math.isfinite(s) or abs(s) > 0.12:
        raise ValueError(
            "X shear coefficient must be finite and within [-0.12, 0.12]"
        )
    if width < 1 or height < 1:
        raise ValueError("Invalid image dimensions")
    pad = 0 if s == 0 else math.ceil(abs(s) * height / 2) + 2
    return {
        "coefficient": s,
        "source_resolution": [width, height],
        "output_resolution": [width + 2 * pad, height],
        "horizontal_padding_px": pad,
        "matrix": [[1.0, s, pad - s * height / 2], [0.0, 1.0, 0.0]],
        "definition": "x_out=x+s*(y-height/2)+pad; y_out=y",
        "interpolation": "linear in sRGB; edge replication in padding",
        "padding_note": "Translation and horizontal padding prevent clipping; no vertical shear.",
    }


def affine_for_scene(width, height, s, framing, regions):
    """Keep register and annotations in frame while cropping only background.

    Prefer the existing canvas. Add symmetric horizontal padding only when the
    transformed register footprint or refitted OBB would otherwise be clipped.
    """
    affine = affine_for_shape(width, height, s)
    if s == 0:
        return affine
    footprint = (
        framing.get("register_footprint_polygon_px") if framing else None
    )
    if not footprint:
        return affine  # no trusted silhouette: preserve whole canvas
    provisional = copy.deepcopy(affine)
    provisional["horizontal_padding_px"] = 0
    provisional["output_resolution"] = [width, height]
    provisional["matrix"][0][2] = -float(s) * height / 2
    points = map_points(footprint, provisional)
    for region in regions:
        for key in ("visible_boundary_px", "physical_slot_obb_px"):
            transformed = map_points(region[key], provisional)
            points.extend(minimum_rectangle(transformed)[0])
    low = min(p[0] for p in points)
    high = max(p[0] for p in points)
    pad = max(0, math.ceil(2 - low), math.ceil(high - width + 2))
    affine["horizontal_padding_px"] = pad
    affine["output_resolution"] = [width + 2 * pad, height]
    affine["matrix"][0][2] = pad - float(s) * height / 2
    affine["padding_note"] = (
        "Minimal padding protects the register footprint "
        "and OBBs; outer source background may "
        "be cropped."
    )
    affine["canvas_policy"] = "protect_register_and_annotations"
    return affine


def map_points(points, affine):
    s = affine["coefficient"]
    offset = affine["matrix"][0][2]
    return [[float(x + s * y + offset), float(y)] for x, y in points]


def shear_image(rgb, affine):
    """Warp each image row horizontally; peripheral background may be cropped."""
    image = np.asarray(rgb)
    if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected uint8 RGB image")
    h, w = image.shape[:2]
    if [w, h] != affine["source_resolution"]:
        raise ValueError("Image size does not match affine")
    s = affine["coefficient"]
    pad = affine["horizontal_padding_px"]
    outw = affine["output_resolution"][0]
    if s == 0:
        return image.copy()
    result = np.empty((h, outw, 3), dtype=np.uint8)
    dest = np.arange(outw, dtype=np.float64)
    for y in range(h):
        src = np.clip(dest - pad - s * (y - h / 2), 0, w - 1)
        left = np.floor(src).astype(np.intp)
        right = np.minimum(left + 1, w - 1)
        weight = (src - left)[:, None]
        result[y] = np.clip(
            np.rint(image[y, left] * (1 - weight) + image[y, right] * weight),
            0,
            255,
        ).astype(np.uint8)
    return result


def transform_regions(regions, affine):
    """Transform the projected mesh hull, then refit its pixel-metric OBB."""
    out = []
    width, height = affine["output_resolution"]
    for original in regions:
        r = copy.deepcopy(original)
        r["pre_shear_projection"] = {
            k: copy.deepcopy(r[k])
            for k in (
                "visible_boundary_px",
                "obb_px",
                "physical_slot_obb_px",
                "checks",
                "angle_deg",
                "projected_obb_width_to_slot_ratio",
            )
            if k in r
        }
        boundary = map_points(original["visible_boundary_px"], affine)
        box, angle = minimum_rectangle(boundary)
        if any(
            not math.isfinite(v) or not 0 <= v <= [width, height][j]
            for p in box
            for j, v in enumerate(p)
        ):
            raise ValueError("Sheared OBB exceeds output bounds")
        for p in boundary:
            for a, b in zip(box, box[1:] + box[:1]):
                if (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (
                    p[0] - a[0]
                ) < -1e-4:
                    raise ValueError(
                        "Refitted OBB does not contain the sheared contour"
                    )
        slot, _ = minimum_rectangle(
            map_points(original["physical_slot_obb_px"], affine)
        )
        r["visible_boundary_px"] = boundary
        r["obb_px"] = box
        r["physical_slot_obb_px"] = slot
        r["angle_deg"] = angle
        r["physical_slot_obb_note"] = (
            "Conservative rectangle enclosing the sheared pre-shear slot OBB."
        )
        r.pop("projected_obb_width_to_slot_ratio", None)
        r["checks"] = {
            "coverage": "all transformed mesh hull vertices enclosed",
            "boundary_area_px2": area(boundary),
            "obb_area_px2": area(box),
            "boundary_to_obb_area_ratio": area(boundary) / area(box),
        }
        out.append(r)
    return out


def transform_framing(framing, affine):
    result = copy.deepcopy(framing)
    if not result:
        return result
    if "register_footprint_polygon_px" in result:
        result["register_footprint_polygon_px"] = map_points(
            result["register_footprint_polygon_px"], affine
        )
    oldw, oldh = affine["source_resolution"]
    neww, newh = affine["output_resolution"]
    if "register_area_fraction" in result:
        result["register_area_fraction"] *= oldw * oldh / (neww * newh)
        result["background_area_fraction"] = (
            1 - result["register_area_fraction"]
        )
    if "projected_register_roll_deg" in result:
        angle = math.radians(result["projected_register_roll_deg"])
        s = affine["coefficient"]
        result["projected_register_roll_deg"] = math.degrees(
            math.atan2(math.sin(angle), math.cos(angle) + s * math.sin(angle))
        )
    result["image_affine_note"] = (
        "Framing footprint transformed by X shear; original perspective camera remains unchanged."
    )
    return result


def apply_to_file(path, regions, framing, s):
    """Apply the same X shear to a PNG, projected geometry and framing."""
    from .camera_appearance import read_png, write_png

    rgb = read_png(path)
    h, w = rgb.shape[:2]
    affine = affine_for_scene(w, h, s, framing, regions)
    transformed = transform_regions(regions, affine)
    if s != 0:
        write_png(path, shear_image(rgb, affine))
    return (transformed, transform_framing(framing, affine), affine)
