"""Sample white windows with centered gray numeral strips."""

import copy
import json
import sys
from pathlib import Path

import numpy as np

PARENT = Path(__file__).resolve().parents[2]
V1 = PARENT / "2d_mask_4_diffusion_V1"
sys.path.insert(0, str(V1))
from geometry_worker.geometry import boundary, min_area_rect, validate_strip
from geometry_worker.worker import DEFAULT_CONFIG as V1_CONFIG
from geometry_worker.worker import aabb_from_contour, flux_bbox_from_strip
from geometry_worker.worker import jacobian, project, random_parameters

DEFAULT_CONFIG = Path(__file__).with_name("config.json")


def coefficients(center, a, b, curve):
    """Describe the quadratic surface using V1's geometry representation."""
    return {
        "p": center.tolist(),
        "a": a.tolist(),
        "b": b.tolist(),
        "k": curve.tolist(),
    }


def sample(seed, config):
    base = json.loads(V1_CONFIG.read_text())
    count = int(config["window_count"])
    if count not in (5, 6):
        raise ValueError("window_count must be 5 or 6")
    width, height = base["width"], base["height"]
    n = base["boundary_samples_per_edge"]
    rng = np.random.default_rng(seed)
    base["shared_curvature_halfwidth"] = config[
        "shared_curvature_halfwidth"
    ]
    params = random_parameters(rng, base)
    gap = float(rng.uniform(*config["gap_to_window_width"]))
    coverage = float(rng.uniform(*config["window_coverage_fraction"]))
    height_fraction = float(
        rng.uniform(*config["window_height_fraction"])
    )
    fraction = coverage / (count + (count - 1) * gap)
    params["strip_width_fraction"] = fraction
    params["strip_height_fraction"] = height_fraction
    params["gap_to_width_ratio"] = gap
    transform = np.diag([width, height])
    homography = np.asarray(params["homography"])
    center = transform @ project(homography, [0.5, 0.5])
    matrix = transform @ jacobian(homography, [0.5, 0.5])
    a = matrix[:, 0] * (fraction / 2)
    b = matrix[:, 1] * (height_fraction / 2)
    b = b + a * params["shared_slant_halfwidth"]
    curve = a * params["shared_curvature_halfwidth"]
    ratio = float(config["center_strip_width_fraction"])
    if not 0 < ratio < 1:
        raise ValueError("Invalid center strip fraction")
    windows = []
    strips = []
    middle = (count - 1) / 2
    perspective = params["horizontal_perspective"]
    scales = [
        1 / (1 + perspective * (i - middle) * fraction)
        for i in range(count)
    ]
    positions = [0.0]
    for left, right in zip(scales, scales[1:]):
        positions.append(positions[-1] + (left + right) * (1 + gap))
    midpoint = (positions[0] + positions[-1]) / 2
    for index in range(count):
        factor = scales[index]
        point = center + a * (positions[index] - midpoint)
        window = coefficients(point, a * factor, b * factor, curve * factor)
        strip = coefficients(
            point, a * ratio * factor, b * factor, curve * factor
        )
        window_contour = boundary(window, n)
        contour = boundary(strip, n)
        box, area = min_area_rect(contour)
        determinants = validate_strip(
            strip, contour, box, width, height
        )
        window_box, _ = min_area_rect(window_contour)
        validate_strip(window, window_contour, window_box, width, height)
        aabb_px, aabb_normalized = aabb_from_contour(
            contour, width, height
        )
        windows.append({
            "index": index,
            "perspective_scale": factor,
            "coefficients_px": window,
            "contour_px": window_contour.tolist(),
        })
        strips.append({
            "index": index,
            "coefficients_px": strip,
            "fill_gray": int(config["strip_gray"]),
            "contour_px": contour.tolist(),
            "contour_normalized": (contour / [width, height]).tolist(),
            "obb_px": box.tolist(),
            "obb_normalized": (box / [width, height]).tolist(),
            "obb_area_px2": area,
            "aabb_px": aabb_px,
            "aabb_normalized": aabb_normalized,
            "flux_bbox": flux_bbox_from_strip(strip, width, height),
            "jacobian_endpoint_determinants": determinants,
        })
    return {
        "schema_version": 7,
        "seed": int(seed),
        "resolution": [width, height],
        "boundary_samples_per_edge": n,
        "background_gray": int(config["background_gray"]),
        "window_gray": int(config["window_gray"]),
        "windows": windows,
        "strips": strips,
        "sampled_gap_to_window_width": gap,
        "center_strip_width_fraction": ratio,
        "shared_parameters": params,
        "sampling_configuration": copy.deepcopy(config),
        "annotation_target": "center_strip",
        "geometry_note": (
            "Locally affine strip geometry with perspective-inspired "
            "per-window scaling; not an exact projective warp."
        ),
    }
