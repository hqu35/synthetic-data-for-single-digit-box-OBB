"""Sample and validate quadratic strip geometry in pixel coordinates."""

import math
import numpy as np


def boundary(coeff, samples):
    # Four oriented edges, shared end points appear only once.
    q = (
        np.arange(
            samples, dtype=np.float64
        )
        * 2
        / samples
        - 1
    )
    s = np.concatenate(
        (
            q,
            np.ones(samples),
            -q,
            -np.ones(samples),
        )
    )
    t = np.concatenate(
        (
            -np.ones(samples),
            q,
            np.ones(samples),
            -q,
        )
    )
    p, a, b, k = (
        np.asarray(
            coeff[x], dtype=float
        )
        for x in ('p', 'a', 'b', 'k')
    )
    return (
        p
        + np.outer(s, a)
        + np.outer(t, b)
        + np.outer(t * t, k)
    )


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def convex_hull(points):
    pts = sorted(
        set(
            map(
                tuple,
                np.asarray(
                    points, float
                ),
            )
        )
    )

    def orient(o, a, b):
        return cross(
            np.subtract(a, o),
            np.subtract(b, o),
        )

    if len(pts) < 3:
        raise ValueError(
            'Degenerate contour'
        )
    chains = []
    for seq in (pts, reversed(pts)):
        chain = []
        for p in seq:
            while (
                len(chain) >= 2
                and orient(
                    chain[-2],
                    chain[-1],
                    p,
                )
                <= 0
            ):
                chain.pop()
            chain.append(p)
        chains.append(chain[:-1])
    h = chains[0] + chains[1]
    if len(h) < 3:
        raise ValueError(
            'Collinear contour'
        )
    return np.asarray(h)


def min_area_rect(points):
    """Exact minimum rectangle of the sampled polygon's convex hull in pixels."""
    h = convex_hull(points)
    edges = np.roll(h, -1, axis=0) - h
    angles = np.arctan2(
        edges[:, 1], edges[:, 0]
    )
    best = None
    for angle in angles:
        # Equivalent orientations differ by 90 degrees; canonicalize axis.
        angle = (
            angle + math.pi / 4
        ) % (math.pi / 2) - math.pi / 4
        u = np.array(
            [
                math.cos(angle),
                math.sin(angle),
            ]
        )
        v = np.array([-u[1], u[0]])
        x = h @ u
        y = h @ v
        x0, x1 = x.min(), x.max()
        y0, y1 = y.min(), y.max()
        ar = (x1 - x0) * (y1 - y0)
        if best is None or ar < best[0]:
            best = (
                ar,
                u,
                v,
                x0,
                x1,
                y0,
                y1,
            )
    ar, u, v, x0, x1, y0, y1 = best
    box = np.array(
        [
            x0 * u + y0 * v,
            x1 * u + y0 * v,
            x1 * u + y1 * v,
            x0 * u + y1 * v,
        ]
    )
    return box, float(ar)


def points_in_box(
    points, box, tolerance=1e-7
):
    edge = (
        np.roll(box, -1, axis=0) - box
    )
    delta = (
        np.asarray(points)[:, None, :]
        - box[None, :, :]
    )
    crosses = (
        edge[None, :, 0]
        * delta[:, :, 1]
        - edge[None, :, 1]
        * delta[:, :, 0]
    )
    return bool(
        np.all(crosses >= -tolerance)
    )


def simple_polygon(points):
    # Bounding-box broad phase and strict crossings; adjacent edges share endpoints.
    p = np.asarray(points)
    q = np.roll(p, -1, axis=0)
    n = len(p)
    for i in range(n):
        js = np.arange(i + 2, n)
        if i == 0:
            js = js[js != n - 1]
        if not len(js):
            continue
        a, b = p[i], q[i]
        c, d = p[js], q[js]
        broad = (
            np.maximum(
                np.minimum(a[0], b[0]),
                np.minimum(
                    c[:, 0], d[:, 0]
                ),
            )
            <= np.minimum(
                np.maximum(a[0], b[0]),
                np.maximum(
                    c[:, 0], d[:, 0]
                ),
            )
        ) & (
            np.maximum(
                np.minimum(a[1], b[1]),
                np.minimum(
                    c[:, 1], d[:, 1]
                ),
            )
            <= np.minimum(
                np.maximum(a[1], b[1]),
                np.maximum(
                    c[:, 1], d[:, 1]
                ),
            )
        )
        c, d = c[broad], d[broad]
        if not len(c):
            continue
        ab = b - a
        cd = d - c
        ca = c - a
        da = d - a
        ac = a - c
        bc = b - c
        u = (
            ab[0] * ca[:, 1]
            - ab[1] * ca[:, 0]
        )
        v = (
            ab[0] * da[:, 1]
            - ab[1] * da[:, 0]
        )
        w = (
            cd[:, 0] * ac[:, 1]
            - cd[:, 1] * ac[:, 0]
        )
        z = (
            cd[:, 0] * bc[:, 1]
            - cd[:, 1] * bc[:, 0]
        )
        if np.any(
            (u * v <= 0) & (w * z <= 0)
        ):
            return False
    return True


def validate_strip(
    coeff, contour, box, width, height
):
    a, b, k = (
        np.asarray(coeff[x], float)
        for x in ('a', 'b', 'k')
    )
    determinants = [
        cross(a, b + 2 * t * k)
        for t in (-1, 1)
    ]
    if (
        min(
            abs(x) for x in determinants
        )
        < 1e-7
        or determinants[0]
        * determinants[1]
        <= 0
    ):
        raise ValueError(
            'Mapping has singular or folded Jacobian'
        )
    if not simple_polygon(contour):
        raise ValueError(
            'Contour is self-intersecting'
        )
    if not points_in_box(contour, box):
        raise ValueError(
            'OBB does not enclose the sampled contour'
        )
    if (
        not np.all(np.isfinite(box))
        or np.any(box < 0)
        or np.any(box[:, 0] > width)
        or np.any(box[:, 1] > height)
    ):
        raise ValueError(
            'OBB is out of image bounds'
        )
    if (
        abs(
            cross(
                box[1] - box[0],
                box[3] - box[0],
            )
        )
        < 25
    ):
        raise ValueError(
            'OBB too small'
        )
    return determinants
