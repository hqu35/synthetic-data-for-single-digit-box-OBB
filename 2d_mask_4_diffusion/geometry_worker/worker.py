"""Deterministic statistical sampling and reconstructible 2D strip geometry."""

import copy, math
from pathlib import Path
import numpy as np
from .geometry import (
    boundary,
    min_area_rect,
    validate_strip,
)

DEFAULT_CONFIG = Path(
    __file__
).with_name('config.json')


def aabb_from_contour(
    contour, width, height
):
    """Tight sampled-boundary AABB in [xmin, ymin, xmax, ymax] order."""
    points = np.asarray(
        contour, dtype=float
    )
    lo = points.min(axis=0)
    hi = points.max(axis=0)
    box = [
        float(lo[0]),
        float(lo[1]),
        float(hi[0]),
        float(hi[1]),
    ]
    return (
        box,
        (
            np.asarray(box)
            / [
                width,
                height,
                width,
                height,
            ]
        ).tolist(),
    )


def flux_bbox_from_obb(
    obb, width, height
):
    """FLUX guidance AABB of the original OBB, [top,left,bottom,right] on 0..1000."""
    points = np.asarray(
        obb, dtype=float
    )
    lo = points.min(axis=0)
    hi = points.max(axis=0)
    result = [
        round(
            float(lo[1]) / height * 1000
        ),
        round(
            float(lo[0]) / width * 1000
        ),
        round(
            float(hi[1]) / height * 1000
        ),
        round(
            float(hi[0]) / width * 1000
        ),
    ]
    if not (
        0
        <= result[0]
        < result[2]
        <= 1000
        and 0
        <= result[1]
        < result[3]
        <= 1000
    ):
        raise ValueError(
            'Invalid FLUX guidance box'
        )
    return result


def flux_bbox_from_strip_corners(
    contour, samples, width, height
):
    """Axis-aligned rectangle anchored at the strip's top-left and bottom-right."""
    points = np.asarray(
        contour, dtype=float
    )
    if len(points) != 4 * samples:
        raise ValueError(
            'Unexpected strip boundary length'
        )
    top_left = points[0]
    bottom_right = points[2 * samples]
    result = [
        round(
            float(top_left[1])
            / height
            * 1000
        ),
        round(
            float(top_left[0])
            / width
            * 1000
        ),
        round(
            float(bottom_right[1])
            / height
            * 1000
        ),
        round(
            float(bottom_right[0])
            / width
            * 1000
        ),
    ]
    if not (
        0
        <= result[0]
        < result[2]
        <= 1000
        and 0
        <= result[1]
        < result[3]
        <= 1000
    ):
        raise ValueError(
            'Invalid FLUX corner-anchored box'
        )
    return result


def flux_bbox_from_strip(
    coeff, width, height
):
    """Enclose the complete quadratic strip boundary on the integer 0..1000 grid."""
    p, a, b, k = (
        np.asarray(
            coeff[name], dtype=float
        )
        for name in ('p', 'a', 'b', 'k')
    )
    points = []
    for s in (-1.0, 1.0):
        ts = [-1.0, 1.0]
        for axis in (0, 1):
            if k[axis] != 0:
                t = -b[axis] / (
                    2 * k[axis]
                )
                if -1 < t < 1:
                    ts.append(float(t))
        points.extend(
            p
            + a * s
            + b * t
            + k * t * t
            for t in ts
        )
    points = np.asarray(points)
    lo = points.min(axis=0)
    hi = points.max(axis=0)
    if not (
        np.all(np.isfinite(points))
        and 0 <= lo[0] < hi[0] <= width
        and 0 <= lo[1] < hi[1] <= height
    ):
        raise ValueError(
            'FLUX strip is outside the image'
        )
    result = [
        math.floor(
            float(lo[1]) / height * 1000
        ),
        math.floor(
            float(lo[0]) / width * 1000
        ),
        math.ceil(
            float(hi[1]) / height * 1000
        ),
        math.ceil(
            float(hi[0]) / width * 1000
        ),
    ]
    if not (
        0
        <= result[0]
        < result[2]
        <= 1000
        and 0
        <= result[1]
        < result[3]
        <= 1000
    ):
        raise ValueError(
            'Invalid FLUX strip box'
        )
    return result


def project(H, xy):
    v = H @ np.array(
        [xy[0], xy[1], 1.0]
    )
    if v[2] <= 0.2:
        raise ValueError(
            'Invalid projective depth'
        )
    return v[:2] / v[2]


def jacobian(H, xy):
    den = (H @ np.array([*xy, 1.0]))[2]
    p = project(H, xy)
    return (
        H[:2, :2]
        - np.outer(p, H[2, :2])
    ) / den


def random_parameters(rng, c):
    pick = lambda name: float(
        rng.uniform(*c[name])
    )
    w = pick('strip_width_fraction')
    h = pick('strip_height_fraction')
    gap = pick('gap_to_width_ratio')
    roll = pick('global_roll_deg')
    qx = pick('horizontal_perspective')
    qy = pick('vertical_perspective')
    sx = pick(
        'horizontal_foreshortening'
    )
    sy = pick('vertical_scale')
    slant = pick(
        'shared_slant_halfwidth'
    )
    bend = pick(
        'shared_curvature_halfwidth'
    )
    angle = math.radians(roll)
    co, si = math.cos(angle), math.sin(
        angle
    )
    ratio = c['height'] / c['width']
    # Rotation is applied in pixel metric despite normalized x/y coordinates.
    R = np.array(
        [
            [co, -si * ratio, 0],
            [si / ratio, co, 0],
            [0, 0, 1.0],
        ]
    )
    S = np.diag([sx, sy, 1])
    P = np.array(
        [
            [1.0, 0, 0],
            [0, 1.0, 0],
            [qx, qy, 1.0],
        ]
    )
    T = np.array(
        [
            [1.0, 0, 0.5],
            [0, 1.0, 0.5],
            [0, 0, 1.0],
        ]
    )
    H = (
        T
        @ P
        @ R
        @ S
        @ np.array(
            [
                [1.0, 0, -0.5],
                [0, 1.0, -0.5],
                [0, 0, 1.0],
            ]
        )
    )
    return {
        'strip_width_fraction': w,
        'strip_height_fraction': h,
        'gap_to_width_ratio': gap,
        'global_roll_deg': roll,
        'horizontal_perspective': qx,
        'vertical_perspective': qy,
        'horizontal_foreshortening': sx,
        'vertical_scale': sy,
        'shared_slant_halfwidth': slant,
        'shared_curvature_halfwidth': bend,
        'homography': H.tolist(),
    }


def sample(seed, c):
    width, height = int(
        c['width']
    ), int(c['height'])
    n = int(
        c['boundary_samples_per_edge']
    )
    if (
        width < 64
        or height < 64
        or n < 16
        or n > 1024
    ):
        raise ValueError(
            'Invalid canvas or contour sampling resolution'
        )
    rng = np.random.default_rng(seed)
    D = np.diag([width, height])
    for attempt in range(
        int(c['max_attempts'])
    ):
        try:
            p = random_parameters(
                rng, c
            )
            H = np.asarray(
                p['homography']
            )
            w = p[
                'strip_width_fraction'
            ]
            h = p[
                'strip_height_fraction'
            ]
            pitch = w * (
                1
                + p[
                    'gap_to_width_ratio'
                ]
            )
            background = int(
                rng.integers(
                    c[
                        'background_gray'
                    ][0],
                    c[
                        'background_gray'
                    ][1]
                    + 1,
                )
            )
            gray = int(
                rng.integers(
                    c['strip_gray'][0],
                    c['strip_gray'][1]
                    + 1,
                )
            )
            strips = []
            axis = (
                D
                @ jacobian(
                    H, [0.5, 0.5]
                )[:, 0]
            )
            axis /= np.linalg.norm(axis)
            for i in range(5):
                center = [
                    0.5
                    + (i - 2) * pitch,
                    0.5,
                ]
                J = jacobian(H, center)
                point = D @ project(
                    H, center
                )
                wf = 1 + float(
                    rng.uniform(
                        *c[
                            'local_width_deviation'
                        ]
                    )
                )
                hf = 1 + float(
                    rng.uniform(
                        *c[
                            'local_height_deviation'
                        ]
                    )
                )
                local_bend = p[
                    'shared_curvature_halfwidth'
                ] + float(
                    rng.uniform(
                        *c[
                            'local_curvature_deviation'
                        ]
                    )
                )
                a = (
                    D
                    @ J[:, 0]
                    * (w / 2)
                    * wf
                )
                b = (
                    D
                    @ J[:, 1]
                    * (h / 2)
                    * hf
                    + a
                    * p[
                        'shared_slant_halfwidth'
                    ]
                )
                k = a * local_bend
                coeff = {
                    'p': point.tolist(),
                    'a': a.tolist(),
                    'b': b.tolist(),
                    'k': k.tolist(),
                }
                contour = boundary(
                    coeff, n
                )
                box, area = (
                    min_area_rect(
                        contour
                    )
                )
                det = validate_strip(
                    coeff,
                    contour,
                    box,
                    width,
                    height,
                )
                (
                    aabb_px,
                    aabb_normalized,
                ) = aabb_from_contour(
                    contour,
                    width,
                    height,
                )
                delta = int(
                    rng.integers(
                        c[
                            'local_gray_delta'
                        ][0],
                        c[
                            'local_gray_delta'
                        ][1]
                        + 1,
                    )
                )
                color = max(
                    0,
                    min(
                        255,
                        gray + delta,
                    ),
                )
                strips.append(
                    {
                        'index': i,
                        'coefficients_px': coeff,
                        'fill_gray': color,
                        'contour_px': contour.tolist(),
                        'contour_normalized': (
                            contour
                            / [
                                width,
                                height,
                            ]
                        ).tolist(),
                        'obb_px': box.tolist(),
                        'obb_normalized': (
                            box
                            / [
                                width,
                                height,
                            ]
                        ).tolist(),
                        'obb_area_px2': area,
                        'aabb_px': aabb_px,
                        'aabb_normalized': aabb_normalized,
                        'flux_bbox': flux_bbox_from_strip(
                            coeff,
                            width,
                            height,
                        ),
                        'jacobian_endpoint_determinants': det,
                        'local_width_multiplier': wf,
                        'local_height_multiplier': hf,
                        'local_curvature_halfwidth': local_bend,
                        'quadratic_side_max_chord_error_px': float(
                            np.linalg.norm(
                                k
                            )
                            / (n * n)
                        ),
                    }
                )
            # Require a separating line between each pair in the
            # common assembly axis.
            intervals = [
                (
                    np.min(
                        np.asarray(
                            x[
                                'contour_px'
                            ]
                        )
                        @ axis
                    ),
                    np.max(
                        np.asarray(
                            x[
                                'contour_px'
                            ]
                        )
                        @ axis
                    ),
                )
                for x in strips
            ]
            gaps = [
                float(
                    intervals[i + 1][0]
                    - intervals[i][1]
                )
                for i in range(4)
            ]
            if any(
                g <= 1 for g in gaps
            ):
                raise ValueError(
                    'Strips overlap or have no positive separation'
                )
            return {
                'schema_version': 6,
                'seed': int(seed),
                'resolution': [
                    width,
                    height,
                ],
                'boundary_samples_per_edge': n,
                'background_gray': background,
                'shared_parameters': p,
                'sampling_configuration': copy.deepcopy(
                    c
                ),
                'attempt': attempt,
                'separation_axis_px': axis.tolist(),
                'minimum_separation_gaps_px': gaps,
                'strips': strips,
                'geometry_definition': 'F_i(s,t)=p_i+a_i*s+b_i*t+k_i*t^2 in pixels; s,t in [-1,1].',
                'annotation_definition': (
                    'YOLO class 0 plus four OBB '
                    'vertices normalized to [0,1]; FLUX rectangle '
                    'encloses the full continuous strip boundary '
                    'in [top,left,bottom,right] order on [0,1000], rounded '
                    'outward.'
                ),
                'sampling_status': 'provisional, not empirically calibrated',
            }
        except ValueError:
            continue
    raise RuntimeError(
        f'Could not sample a valid assembly in {c["max_attempts"]} attempts for seed {seed}'
    )


def reconstruct(data):
    n = data[
        'boundary_samples_per_edge'
    ]
    width, height = data['resolution']
    result = copy.deepcopy(data)
    for strip in result['strips']:
        contour = boundary(
            strip['coefficients_px'], n
        )
        box, area = min_area_rect(
            contour
        )
        det = validate_strip(
            strip['coefficients_px'],
            contour,
            box,
            width,
            height,
        )
        strip.update(
            contour_px=contour.tolist(),
            contour_normalized=(
                contour
                / [width, height]
            ).tolist(),
            obb_px=box.tolist(),
            obb_normalized=(
                box / [width, height]
            ).tolist(),
            obb_area_px2=area,
            jacobian_endpoint_determinants=det,
        )
        if (
            result.get(
                'schema_version', 1
            )
            >= 2
        ):
            (
                strip['aabb_px'],
                strip[
                    'aabb_normalized'
                ],
            ) = aabb_from_contour(
                contour, width, height
            )
        if (
            result.get(
                'schema_version', 1
            )
            == 3
        ):
            strip['flux_bbox'] = (
                flux_bbox_from_obb(
                    box, width, height
                )
            )
        if (
            result.get(
                'schema_version', 1
            )
            == 4
        ):
            strip['flux_bbox'] = (
                flux_bbox_from_strip_corners(
                    contour,
                    n,
                    width,
                    height,
                )
            )
        if (
            result.get(
                'schema_version', 1
            )
            >= 5
        ):
            strip['flux_bbox'] = (
                flux_bbox_from_strip(
                    strip[
                        'coefficients_px'
                    ],
                    width,
                    height,
                )
            )
    return result


def upgrade_to_aabb(data):
    """Upgrade legacy geometry to dual annotations without altering its shape."""
    result = copy.deepcopy(data)
    result['schema_version'] = 6
    result.pop('reading', None)
    for strip in result['strips']:
        strip.pop('digit', None)
    result['annotation_definition'] = (
        (
            'YOLO class 0 plus four OBB '
            'vertices normalized to [0,1]; FLUX rectangle '
            'encloses the full continuous strip boundary '
            'in [top,left,bottom,right] order on [0,1000], rounded '
            'outward.'
        )
    )
    return reconstruct(result)
