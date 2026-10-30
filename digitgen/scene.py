"""Blender-only scene construction and camera projection adapter."""
import math
from pathlib import Path
import bpy
from mathutils import Vector, Quaternion, Matrix
from bpy_extras.object_utils import world_to_camera_view
from .geometry import aperture_corners, minimum_rectangle, angle_delta, convex_intersection
from .mechanics import build_register
from .assets import verify_spec


def project(scene, camera, points, resolution):
    result = []
    for p in points:
        ndc = world_to_camera_view(scene, camera, Vector(p))
        if ndc.z <= camera.data.clip_start or ndc.z >= camera.data.clip_end:
            raise ValueError('Boundary behind camera or outside depth range')
        result.append([ndc.x*resolution[0], (1-ndc.y)*resolution[1]])
    return result


def create_scene(c, p):
    verify_spec(p['texture'])
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Clear orphan data across samples so batch memory remains bounded.
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for item in list(collection):
            if item.users == 0:
                collection.remove(item)
    for image in list(bpy.data.images):
        if image.users==0 and image.name not in ('Render Result','Viewer Node'):
            bpy.data.images.remove(image)
    scene = bpy.context.scene
    scene.render.engine = c['render']['engine']
    scene.cycles.device = 'CPU'
    scene.cycles.samples = c['render']['samples']
    scene.cycles.use_denoising = c['render']['denoise']
    scene.cycles.seed = p['seed'] % 2147483647
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = c['render']['threads']
    scene.render.resolution_x, scene.render.resolution_y = c['resolution']
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.exposure = 0
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.8,0.8,0.8,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = p['lighting']['world_strength']
    n,w,h,r,pitch=p['digit_count'],p['slot_width'],p['slot_height'],p['wheel_radius'],p['pitch']
    centers,z,frame_depth=build_register(c,p,Path(__file__).resolve().parents[1])
    border=c['geometry']['frame_border']
    half_width=((n-1)*pitch+w)/2
    target = Vector((0,0,z))
    camera_data = bpy.data.cameras.new('Camera')
    camera = bpy.data.objects.new('Camera', camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    cp = p['camera']
    yaw, tilt, distance = math.radians(cp['yaw_deg']), math.radians(cp['pitch_deg']), cp['distance']
    camera.location = target + Vector((math.sin(yaw)*math.cos(tilt), math.sin(tilt), math.cos(yaw)*math.cos(tilt)))*distance
    # Explicit world +Y up avoids to_track_quat's world-Z roll ambiguity near frontal.
    forward = (target-camera.location).normalized()
    right = forward.cross(Vector((0,1,0))).normalized()
    up = right.cross(forward).normalized()
    base = Matrix((right, up, -forward)).transposed().to_quaternion()
    camera.rotation_mode = 'QUATERNION'
    camera.data.type = cp['projection']
    camera.data.lens_unit = 'FOV'
    camera.data.angle = math.radians(cp['fov_deg'])
    camera.data.ortho_scale = 8
    camera.data.clip_start, camera.data.clip_end = .1, 200
    central = aperture_corners(0,w,h,z)
    roll = 0.0
    # Solve roll using measured pixel-space OBB angles, including sign calibration.
    def measure(value):
        camera.rotation_quaternion = base @ Quaternion((0,0,1), math.radians(value))
        bpy.context.view_layer.update()
        return minimum_rectangle(project(scene,camera,central,c['resolution']))[1]
    # Measure sign on the physical width centerline. Differentiating the fitted
    # minimum-area rectangle is unstable when two nearly equal candidate edges
    # exchange places; its width/height ambiguity must never drive a 90deg jump.
    def width_angle(value):
        measure(value)
        line = project(scene,camera,[(-w/2,0,z),(w/2,0,z)],c['resolution'])
        return math.degrees(math.atan2(line[1][1]-line[0][1],line[1][0]-line[0][0]))
    slope = angle_delta(width_angle(1),width_angle(0))
    if abs(abs(slope)-1)>.01:
        raise ValueError('Unexpected camera roll response in final pixel coordinates')
    for _ in range(6):
        actual = measure(roll)
        error = angle_delta(p['requested_angle_deg'], actual)
        if abs(error)<.001:
            break
        roll += error/slope
        if abs(roll)>40:
            raise ValueError('Camera roll calibration exceeded supported crop rotation')
    measure(roll)
    outer = aperture_corners(0, 2*(half_width+border), h+2*border, z)
    # Fit directly to final pixel coordinates, preserving the configured margin.
    for _ in range(3):
        projected = project(scene,camera,outer,c['resolution'])
        margin = c['camera']['margin_fraction']
        factor = max(abs(coord/c['resolution'][j]-.5)/(.5-margin) for pnt in projected for j,coord in enumerate(pnt))
        if camera.data.type=='ORTHO':
            camera.data.ortho_scale *= factor
        else:
            camera.data.lens /= factor
        bpy.context.view_layer.update()
    boundaries = project_regions(scene,camera,centers,w,h,z,frame_depth,c['resolution'])
    boxes = [minimum_rectangle(boundary)[0] for boundary in boundaries]
    cp.update({'position':list(camera.location), 'quaternion_wxyz':list(camera.rotation_quaternion),
               'solved_roll_deg':roll, 'lens_mm':camera.data.lens, 'actual_fov_deg':math.degrees(camera.data.angle),
               'ortho_scale':camera.data.ortho_scale, 'clip_start':camera.data.clip_start, 'clip_end':camera.data.clip_end,
               'matrix_world':[list(row) for row in camera.matrix_world],
               'projection_matrix':[list(row) for row in camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(), x=c['resolution'][0], y=c['resolution'][1])]})
    # Confirm each aperture ray first hits its own wheel/marking, never a neighbor.
    depsgraph = bpy.context.evaluated_depsgraph_get()
    tested = 0
    inverse_rotation = camera.matrix_world.to_3x3()
    for i, x in enumerate(centers):
        for fx in (-.499, 0, .499):
            for fy in (-.499, 0, .499):
                point = Vector((x+fx*w,fy*h,z-frame_depth))
                direction = ((point-camera.location).normalized() if camera.data.type=='PERSP'
                             else inverse_rotation @ Vector((0,0,-1)))
                origin = point+direction*.00001
                hit, _, _, _, obj, _ = scene.ray_cast(depsgraph, origin, direction)
                if not hit or not obj.name.startswith(f'wheel_{i}_'):
                    raise ValueError(f'Aperture {i} occluded or not covered by its physical wheel')
                tested += 1
    p['visibility_rays_checked'] = tested
    p['aperture_z'] = z
    p['aperture_frame_depth'] = frame_depth
    p['annotation_region'] = 'intersection of projected front/back openings of solid frame; excludes inner reveal walls'
    p['aperture_world_boundaries'] = [aperture_corners(x,w,h,z) for x in centers]
    p['projected_boundaries_px'] = boundaries
    # Broad ambient/local illumination; color temperature is separate from plastic.
    light=p['lighting']; temperature=light['temperature_kelvin']
    color=(1.0,max(.75,min(1.0,temperature/6500)),max(.65,min(1.0,temperature/6500))) if temperature<6500 else (6500/temperature, .97, 1)
    for name, energy, location in [
        ('key',light['key_energy'],(light['key_x'],light['key_y'],z+light['height'])),
        ('fill',light['fill_energy'],(light['fill_x'],light['fill_y'],z+light['height']))]:
        data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK'
        data.size=light['area_size'];data.color=color
        obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
        obj.location=location;obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
    if p['photograph']['defocus_enabled']:
        camera.data.dof.use_dof=True
        camera.data.dof.focus_distance=distance
        camera.data.dof.aperture_fstop=p['photograph']['defocus_fstop']
    p['lighting']['resolved_lights'] = [{'name':o.name, 'position':list(o.location), 'energy':o.data.energy,
                                       'color':list(o.data.color), 'size':o.data.size} for o in scene.objects if o.type=='LIGHT']
    return scene, boxes, boundaries


def project_regions(scene,camera,centers,width,height,z,depth,resolution):
    return [convex_intersection(project(scene,camera,aperture_corners(x,width,height,z),resolution),
                                project(scene,camera,aperture_corners(x,width,height,z-depth),resolution)) for x in centers]
