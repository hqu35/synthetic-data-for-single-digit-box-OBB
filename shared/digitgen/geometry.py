"""Pure Python image geometry. Pixels use x right, y down; angles clockwise."""
import math


def area(points):
    return sum(a[0]*b[1] - b[0]*a[1] for a, b in zip(points, points[1:]+points[:1])) / 2


def angle_delta(a, b):
    return (a - b + 90) % 180 - 90


def hull(points):
    points = sorted(set(tuple(p) for p in points))
    if len(points) < 3:
        raise ValueError("Degenerate projected region")
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    chains = []
    for seq in (points, list(reversed(points))):
        chain = []
        for p in seq:
            while len(chain) >= 2 and cross(chain[-2], chain[-1], p) <= 0:
                chain.pop()
            chain.append(p)
        chains.append(chain[:-1])
    result = chains[0] + chains[1]
    if len(result) < 3:
        raise ValueError("Collinear projected boundary")
    return result


def minimum_rectangle(points):
    """Minimum-area enclosing rectangle, canonical near-horizontal width axis.

    Fit in pixels, NEVER normalized coordinates (which distort the metric).
    Return clockwise corners [local TL, TR, BR, BL] and width-axis angle.
    """
    if any(len(p)!=2 or any(not math.isfinite(v) for v in p) for p in points):
        raise ValueError('Nonfinite or malformed projected boundary')
    boundary = hull(points)
    candidates = []
    for a, b in zip(boundary, boundary[1:]+boundary[:1]):
        theta = math.atan2(b[1]-a[1], b[0]-a[0])
        theta = (theta + math.pi/4) % (math.pi/2) - math.pi/4
        u = (math.cos(theta), math.sin(theta))
        v = (-u[1], u[0])
        xs = [p[0]*u[0]+p[1]*u[1] for p in boundary]
        ys = [p[0]*v[0]+p[1]*v[1] for p in boundary]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        corners = [[x*u[0]+y*v[0], x*u[1]+y*v[1]] for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]]
        candidates.append(((x1-x0)*(y1-y0), corners, math.degrees(theta)))
    _, corners, theta = min(candidates, key=lambda c: c[0])
    if area(corners) <= 1e-8:
        raise ValueError("Zero-area OBB")
    return corners, theta


def aperture_corners(center_x, width, height, z):
    return [(center_x-width/2, height/2, z), (center_x+width/2, height/2, z),
            (center_x+width/2, -height/2, z), (center_x-width/2, -height/2, z)]


def convex_intersection(subject,clip):
    """Visible opening of a solid frame = intersection of front/back openings."""
    subject=hull(subject);clip=hull(clip)
    for a,b in zip(clip,clip[1:]+clip[:1]):
        def side(p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        output=[]
        for p,q in zip(subject,subject[1:]+subject[:1]):
            sp,sq=side(p),side(q)
            if sp>=0:output.append(p)
            if (sp<0)!=(sq<0):
                t=sp/(sp-sq);output.append([p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])])
        subject=output
        if not subject:raise ValueError('Frame completely occludes viewing aperture')
    return subject


def validate_boxes(boxes, boundaries, resolution, requested, rotation):
    width, height = resolution
    if not boxes or len(boxes)!=len(boundaries):
        raise ValueError('Missing boxes or mismatched boundary count')
    angles, centers = [], []
    for box, boundary in zip(boxes, boundaries):
        if len(box) != 4 or any(not math.isfinite(c) for p in box for c in p):
            raise ValueError("Nonfinite or malformed OBB")
        if any(not (0 <= x <= width and 0 <= y <= height) for x, y in box):
            raise ValueError("Projected OBB outside final image; no clamping allowed")
        if area(box) < 25:
            raise ValueError("OBB too small or incorrectly ordered")
        a, b, c, d = box
        e, f = (b[0]-a[0], b[1]-a[1]), (c[0]-b[0], c[1]-b[1])
        if abs(e[0]*f[0]+e[1]*f[1]) > 1e-5 * math.hypot(*e)*math.hypot(*f):
            raise ValueError("OBB is not rectangular")
        if max(abs(a[j]+c[j]-b[j]-d[j]) for j in (0,1)) > 1e-5:
            raise ValueError('OBB opposite sides are not parallel')
        if min(math.hypot(*e), math.hypot(*f)) < 5:
            raise ValueError("Degenerate OBB dimension")
        for p in boundary:
            for q, r in zip(box, box[1:]+box[:1]):
                if (r[0]-q[0])*(p[1]-q[1])-(r[1]-q[1])*(p[0]-q[0]) < -1e-4:
                    raise ValueError("OBB does not enclose projected aperture")
        theta = math.degrees(math.atan2(e[1], e[0]))
        if not rotation['min_deg']-rotation['tolerance_deg'] <= abs(theta) <= rotation['max_deg']+rotation['tolerance_deg']:
            raise ValueError("Measured OBB angle outside configured nonzero range")
        if theta*requested <= 0 or abs(angle_delta(theta, requested)) > rotation['tolerance_deg']:
            raise ValueError("Requested/measured image angle mismatch")
        angles.append(theta)
        centers.append([sum(p[j] for p in box)/4 for j in (0,1)])
    if max(angles)-min(angles) > rotation['max_spread_deg']:
        raise ValueError("Inconsistent within-register orientation")
    u = (math.cos(math.radians(requested)), math.sin(math.radians(requested)))
    if any((b[0]-a[0])*u[0]+(b[1]-a[1])*u[1] <= 0 for a,b in zip(centers, centers[1:])):
        raise ValueError("Incorrect digit ordering")
    return angles
