"""Mesh-derived visible numeral-band annotations for the approved raised register.

Projects the evaluated printed outer surface, clips each visible facet against
the solid window opening and fits a minimum-area rectangle in pixel coordinates.
No glyph thresholding, 2D scaling or nominal 70% value enters the projection.
"""
import math
import bpy
from mathutils import Vector
from .scene import project
from .geometry import area, hull, convex_intersection, minimum_rectangle


def mesh_bounds_in_register(obj, register):
    transform = register.matrix_world.inverted() @ obj.matrix_world
    vertices = [transform @ v.co for v in obj.data.vertices]
    return [[min(v[j] for v in vertices), max(v[j] for v in vertices)] for j in range(3)]


def physical_slots(register, prefix='front_review_row_', count=5):
    """Read actual inner faces of lips/separators, in register coordinates."""
    def bounds(suffix):
        return mesh_bounds_in_register(bpy.data.objects[prefix+suffix], register)
    top, bottom = bounds('top_lip'), bounds('bottom_lip')
    left, right = bounds('left_lip'), bounds('right_lip')
    separators = [bounds(f'separator_{i}') for i in range(count-1)]
    result = []
    for i in range(count):
        x0 = left[0][1] if i == 0 else separators[i-1][0][1]
        x1 = right[0][0] if i == count-1 else separators[i][0][0]
        y0, y1 = bottom[1][1], top[1][0]
        z0, z1 = top[2]
        if not x0 < x1 or not y0 < y1 or not z0 < z1:
            raise ValueError('Invalid physical window dimensions')
        result.append({'wheel':i, 'x_min':x0, 'x_max':x1, 'y_min':y0,
                       'y_max':y1, 'back_z':z0, 'front_z':z1,
                       'width':x1-x0, 'height':y1-y0})
    return result


def opening_polygon(scene, camera, slot, register, resolution):
    planes = []
    for z in (slot['front_z'], slot['back_z']):
        points = [(slot['x_min'],slot['y_min'],z), (slot['x_max'],slot['y_min'],z),
                  (slot['x_max'],slot['y_max'],z), (slot['x_min'],slot['y_max'],z)]
        planes.append(project(scene,camera,[register.matrix_world @ Vector(p) for p in points],resolution))
    return convex_intersection(*planes)


def validate_enclosing_rectangle(box, boundary, resolution):
    if len(box) != 4 or area(box) <= 1e-8:
        raise ValueError('Degenerate or incorrectly ordered numeral-band OBB')
    if any(not math.isfinite(v) or not 0 <= v <= resolution[j] for p in box for j,v in enumerate(p)):
        raise ValueError('Numeral-band OBB outside image; never clamp labels')
    edges = [(b[0]-a[0],b[1]-a[1]) for a,b in zip(box,box[1:]+box[:1])]
    if abs(sum(a*b for a,b in zip(edges[0],edges[1]))) > 1e-6*math.hypot(*edges[0])*math.hypot(*edges[1]):
        raise ValueError('OBB is not rectangular')
    if any(abs(edges[i][j]+edges[i+2][j])>1e-5 for i in (0,1) for j in (0,1)):
        raise ValueError('OBB opposite edges disagree')
    for p in boundary:
        for a,b in zip(box,box[1:]+box[:1]):
            if (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]) < -1e-4:
                raise ValueError('Numeral-band boundary escapes OBB')
    return {'coverage':'all clipped surface vertices enclosed',
            'boundary_area_px2':area(boundary), 'obb_area_px2':area(box),
            'boundary_to_obb_area_ratio':area(boundary)/area(box)}


def project_numeral_bands(scene, camera, register, resolution, count=5):
    # Blender derives camera framing from scene render aspect, independently of
    # the pixel dimensions supplied to project(). Never mix those two metrics.
    actual=[round(scene.render.resolution_x*scene.render.resolution_percentage/100),
            round(scene.render.resolution_y*scene.render.resolution_percentage/100)]
    if list(resolution)!=actual:
        raise ValueError('Projection resolution must match actual scene render resolution/aspect')
    deps = bpy.context.evaluated_depsgraph_get()
    records = []
    for slot in physical_slots(register,count=count):
        index = slot['wheel']; band = bpy.data.objects[f'wheel_{index}_raised_band']
        if band.hide_render:
            continue
        aperture = opening_polygon(scene,camera,slot,register,resolution)
        full_box,_ = minimum_rectangle(aperture)
        bounds = mesh_bounds_in_register(band, register)
        band_width = bounds[0][1]-bounds[0][0]
        left = bounds[0][0]-slot['x_min']; right = slot['x_max']-bounds[0][1]
        if min(left,right) <= 0:
            raise ValueError('Numeral band is not inside its own physical slot')
        evaluated = band.evaluated_get(deps); mesh = evaluated.to_mesh()
        transform = evaluated.matrix_world
        normal_transform = transform.to_3x3().inverted().transposed()
        clipped = []; visible_faces = 0
        try:
            for face in mesh.polygons:
                # Material 0 is the full printed outer surface, independent of
                # black glyph values. Reject axial annular shoulder faces.
                if face.material_index != 0 or abs(face.normal.x) > .999:
                    continue
                normal = (normal_transform @ face.normal).normalized()
                center = transform @ face.center
                view = (camera.matrix_world.translation-center if camera.data.type=='PERSP'
                        else camera.matrix_world.to_3x3() @ Vector((0,0,1)))
                if normal.dot(view) <= 0:
                    continue
                points = project(scene,camera,[transform @ mesh.vertices[j].co for j in face.vertices],resolution)
                try:
                    polygon = convex_intersection(points,aperture)
                    if len(polygon) < 3 or abs(area(polygon)) < 1e-8:
                        continue
                except ValueError as exc:
                    if str(exc) not in ('Frame completely occludes viewing aperture','Degenerate projected region','Collinear projected boundary'):
                        raise
                    continue
                clipped.extend(polygon); visible_faces += 1
        finally:
            evaluated.to_mesh_clear()
        if not clipped:
            raise ValueError(f'Wheel {index} has no visible printed numeral band')
        boundary = hull(clipped); box,angle = minimum_rectangle(boundary)
        checks = validate_enclosing_rectangle(box,boundary,resolution)
        # Measure widths along the projected physical axle direction, not the
        # near-horizontal canonical rectangle axis (which can swap after roll).
        xmid=(slot['x_min']+slot['x_max'])/2; ymid=(slot['y_min']+slot['y_max'])/2
        axis_points = [register.matrix_world @ Vector((x,ymid,slot['front_z'])) for x in (xmid-.1,xmid+.1)]
        a,b=project(scene,camera,axis_points,resolution); axis=(Vector(b)-Vector(a)).normalized()
        def width(points):
            values=[Vector(p).dot(axis) for p in points];return max(values)-min(values)
        records.append({'wheel':index,'band_object':band.name,'physical_slot':slot,
            'band_mesh_bounds_register':bounds,'band_width':band_width,
            'band_to_slot_width_ratio':band_width/slot['width'],
            'left_margin':left,'right_margin':right,
            'left_margin_fraction':left/slot['width'],'right_margin_fraction':right/slot['width'],
            'visible_surface_facets':visible_faces,'visible_boundary_px':boundary,
            'obb_px':box,'angle_deg':angle,'physical_slot_obb_px':full_box,
            'projected_obb_width_to_slot_ratio':width(box)/width(full_box),
            'checks':checks})
    if len(records) != count:
        raise ValueError(f'Expected one visible band per digit ({count}), got {len(records)}')
    return records
