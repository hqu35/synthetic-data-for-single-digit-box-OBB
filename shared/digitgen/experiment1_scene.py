"""Scene transforms, restrained light variation and rotated-slab diagnostics."""
import hashlib
import json
import math
import random
import bpy
from mathutils import Vector,Matrix,Quaternion,Euler
from .scene import project
from .geometry import hull,area,angle_delta


def immutable_signature():
    records=[]
    for o in sorted(bpy.context.scene.objects,key=lambda o:o.name):
        if o.type!='MESH':continue
        # matrix_local is derived by inverse parent multiplication and can pick
        # up float roundoff under intentional root rotation. Hash the stored
        # local transform and parent inverse instead.
        records.append((o.name,list(map(list,o.matrix_basis)),list(map(list,o.matrix_parent_inverse)),[tuple(v.co) for v in o.data.vertices],
            [tuple(p.vertices) for p in o.data.polygons],
            [[tuple(uv.uv) for uv in layer.data] for layer in o.data.uv_layers],
            [(m.type,getattr(m,'width',None),getattr(m,'segments',None)) for m in o.modifiers]))
    records.append([(o.name,list(o.rotation_euler)) for o in bpy.context.scene.objects if o.name.endswith('_axle')])
    records.append([(i.name,hashlib.sha256(bytes(i.packed_file.data)).hexdigest()) for i in bpy.data.images if i.packed_file])
    mat=bpy.data.objects['Continuous_glass_cover'].data.materials[0]
    records.append([(n.name,[(s.name,list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value)
        for s in n.inputs if hasattr(s,'default_value')]) for n in mat.node_tree.nodes])
    return hashlib.sha256(json.dumps(records,sort_keys=True).encode()).hexdigest()


def orient(obj,target,roll=0):
    forward=(Vector(target)-obj.location).normalized()
    right=forward.cross(Vector((0,1,0))).normalized();up=right.cross(forward)
    obj.rotation_mode='QUATERNION'
    obj.rotation_quaternion=Matrix((right,up,-forward)).transposed().to_quaternion()@Quaternion((0,0,1),math.radians(roll))


def apply_parameters(config,p,source):
    scene=bpy.context.scene;root=bpy.data.objects['RegisterHousing'];camera=scene.camera
    rp=p['register'];root.rotation_euler=[math.radians(rp[f'rotation_{axis}_deg']) for axis in 'xyz']
    bpy.context.view_layer.update()
    cp=p['camera'];target=root.matrix_world@Vector((0,0,1.25))
    yaw,pitch=math.radians(cp['yaw_deg']),math.radians(cp['pitch_deg'])
    camera.location=target+cp['distance']*Vector((math.sin(yaw)*math.cos(pitch),math.sin(pitch),math.cos(yaw)*math.cos(pitch)))
    orient(camera,target,cp['roll_deg']);camera.data.lens=cp['focal_length_mm'];camera.data.dof.use_dof=False
    rng=random.Random(p['lighting']['light_seed']);settings=config['lighting'];lights=[]
    base_by_name={item['name']:item for item in source['lights']}
    for obj in sorted((o for o in scene.objects if o.type=='LIGHT'),key=lambda o:o.name):
        base=base_by_name[obj.name];reflection='reflection' in obj.name
        jitter=[rng.uniform(-d,d)*(.45 if reflection else 1) for d in settings['position_jitter_xyz']]
        obj.location=[base['position'][j]+jitter[j] for j in range(3)]
        factor=rng.uniform(*(settings['reflection_intensity_scale'] if reflection else settings['individual_intensity_scale']))
        obj.data.energy=base['energy']*p['lighting']['intensity_scale']*factor
        size=rng.uniform(*settings['area_size_scale']);obj.data.size=base.get('size',base.get('size_x'))*size
        if obj.data.shape=='RECTANGLE':obj.data.size_y=base.get('size_y',obj.data.size_y)*size
        obj.data.color=[base['color'][j]*p['lighting']['temperature_rgb'][j] for j in range(3)]
        if reflection:
            item=next(i for i in source['complete_glass_config']['reflections'] if i['name']==obj.name)
            orient(obj,item['target'])
        else:orient(obj,target)
        lights.append({'name':obj.name,'type':obj.data.type,'shape':obj.data.shape,
            'position':list(obj.location),'quaternion_wxyz':list(obj.rotation_quaternion),
            'energy':obj.data.energy,'size':obj.data.size,'size_y':getattr(obj.data,'size_y',None),'color_rgb':list(obj.data.color)})
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=p['lighting']['world_strength']
    appearance=p['appearance'];changed_materials=[]
    for material in bpy.data.materials:
        if not material.use_nodes:continue
        ramp=material.node_tree.nodes.get('ColorRamp A')
        if ramp is None:continue
        for stop in ramp.color_ramp.elements:
            color=list(stop.color)
            stop.color=[min(1,color[j]*appearance['substrate_color_scale']*appearance['substrate_rgb_gain'][j]) for j in range(3)]+[color[3]]
        changed_materials.append({'material':material.name,'substrate_ramp':[list(e.color) for e in ramp.color_ramp.elements]})
    scene.view_settings.exposure=appearance['exposure_ev']
    scene.render.resolution_x,scene.render.resolution_y=config['resolution'];scene.render.resolution_percentage=100
    scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
    render=config['render'];scene.render.engine=render['engine'];scene.cycles.device=render['device']
    scene.cycles.samples=render['samples'];scene.cycles.seed=p['seed']%2147483647;scene.cycles.use_denoising=render['denoise']
    scene.render.threads_mode='FIXED';scene.render.threads=render['threads'];scene.render.image_settings.color_mode='RGB'
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_depth='8'
    bpy.context.view_layer.update()
    return {'camera_matrix_world':list(map(list,camera.matrix_world)),
        'register_matrix_world':list(map(list,root.matrix_world)),
        'camera_fov_degrees':math.degrees(camera.data.angle),'camera_sensor_width_mm':camera.data.sensor_width,
        'lights':lights,'substrate_materials':changed_materials,
        'world_strength':p['lighting']['world_strength'],'view_transform':scene.view_settings.view_transform,
        'look':scene.view_settings.look,'exposure_ev':scene.view_settings.exposure}


def framing_check(config,source):
    root=bpy.data.objects['RegisterHousing'];scene=bpy.context.scene;d=source['glass_dimensions']
    corners=[root.matrix_world@Vector((x,y,z)) for x in (-d['width']/2-.03,d['width']/2+.03)
        for y in (-d['height']/2-.03,d['height']/2+.03) for z in (d['back_z'],d['front_z'])]
    px=project(scene,scene.camera,corners,config['resolution']);margin=config['camera']['frame_margin_fraction']
    if any(not margin<=p[j]/config['resolution'][j]<=1-margin for p in px for j in (0,1)):
        raise ValueError('Register cover outside configured framing margin')
    return px


def fit_register_camera(config,p):
    """Fit the actual register silhouette, keeping all native camera optics.

    The requested roll is a small final image-space roll; compensating camera
    roll also accounts for independent register rotation. Lens and sensor shift
    are solved before rendering. No image crop, resize or label fitting occurs.
    """
    if not config['camera'].get('auto_fit_register'):return None
    scene=bpy.context.scene;camera=scene.camera;root=bpy.data.objects['RegisterHousing']
    w,h=config['resolution'];bpy.context.view_layer.update()
    objects=[o for o in scene.objects if o.type=='MESH' and
             (o.name=='Continuous_glass_cover' or o.name.startswith('glass_seat_'))]
    points=[o.matrix_world@v.co for o in objects for v in o.data.vertices]
    width_points=[root.matrix_world@Vector((x,0,1.604)) for x in (-1,1)]
    def image_angle():
        a,b=project(scene,camera,width_points,config['resolution'])
        return math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
    base=camera.rotation_quaternion.copy();initial=image_angle()
    camera.rotation_quaternion=base@Quaternion((0,0,1),math.radians(1));bpy.context.view_layer.update()
    slope=angle_delta(image_angle(),initial)
    if abs(abs(slope)-1)>.01:raise ValueError('Unexpected projected roll response')
    camera.rotation_quaternion=base@Quaternion((0,0,1),math.radians(angle_delta(p['camera']['roll_deg'],initial)/slope))
    camera.data.shift_x=camera.data.shift_y=0
    target=p['camera']['target_register_area_fraction']
    for _ in range(3):
        bpy.context.view_layer.update();boundary=hull(project(scene,camera,points,config['resolution']))
        camera.data.lens*=math.sqrt(target*w*h/area(boundary))
        bpy.context.view_layer.update();boundary=hull(project(scene,camera,points,config['resolution']))
        center=[(min(q[j] for q in boundary)+max(q[j] for q in boundary))/2 for j in (0,1)]
        # Probe the installed Blender camera's actual sensor-shift response.
        probe=project(scene,camera,[points[0]],config['resolution'])[0]
        camera.data.shift_x+=.001;bpy.context.view_layer.update()
        shifted=project(scene,camera,[points[0]],config['resolution'])[0]
        camera.data.shift_x-=.001
        sx=(shifted[0]-probe[0])/.001
        camera.data.shift_y+=.001;bpy.context.view_layer.update()
        shifted=project(scene,camera,[points[0]],config['resolution'])[0]
        camera.data.shift_y-=.001
        sy=(shifted[1]-probe[1])/.001
        camera.data.shift_x+=(w/2-center[0])/sx;camera.data.shift_y+=(h/2-center[1])/sy
    bpy.context.view_layer.update();boundary=hull(project(scene,camera,points,config['resolution']))
    fraction=area(boundary)/(w*h)
    if not config['validation']['minimum_register_image_area_fraction']<=fraction<=config['validation']['maximum_register_image_area_fraction']:
        raise ValueError('Tight framing occupancy outside approved 90–95% range')
    if any(not 0<q[0]<w or not 0<q[1]<h for q in boundary):raise ValueError('Tight framing clips register silhouette')
    if not config['camera']['focal_length_mm'][0]<=camera.data.lens<=config['camera']['focal_length_mm'][1]:
        raise ValueError('Fitted focal length outside configured lens range')
    return {'register_area_fraction':fraction,'background_area_fraction':1-fraction,'register_footprint_polygon_px':boundary,
            'projected_register_roll_deg':image_angle(),'fitted_focal_length_mm':camera.data.lens,
            'sensor_shift_xy':[camera.data.shift_x,camera.data.shift_y],
            'note':'Projected register silhouette fitted by lens and sensor shift before rendering. Focal length is coupled to distance and occupancy by the framing constraint.'}


def perspective_check(config,source):
    """Measure convergence of the actual 3D glass front, not a 2D post-warp."""
    c=config['camera'];minimum=c.get('min_perspective_disparity')
    if minimum is None:return None
    scene=bpy.context.scene;camera=scene.camera;root=bpy.data.objects['RegisterHousing']
    if camera.data.type!='PERSP':raise ValueError('Perspective review requires a perspective camera')
    d=source['glass_dimensions'];w=d['width']/2;h=d['height']/2;z=d['front_z']
    local=[(-w,h,z),(w,h,z),(w,-h,z),(-w,-h,z)]
    points=project(scene,camera,[root.matrix_world@Vector(v) for v in local],config['resolution'])
    left=math.dist(points[0],points[3]);right=math.dist(points[1],points[2])
    disparity=(right-left)/((right+left)/2)
    if not minimum<=abs(disparity)<=c['max_perspective_disparity']:
        raise ValueError('Projected opposite-edge disparity is outside the review range')
    return {'camera_projection':'PERSP','glass_front_quad_px':points,
            'left_edge_height_px':left,'right_edge_height_px':right,
            'signed_opposite_edge_disparity':disparity,
            'definition':'(right edge height - left edge height) / mean edge height; nonzero signals 3D perspective convergence.',
            'geometry':'Four actual 3D glass-front corners projected by the active camera; no image-space warp.'}


def optical_check(config,regions,source):
    """Snell solve in the rigid register frame, then project the world air ray."""
    scene=bpy.context.scene;root=bpy.data.objects['RegisterHousing'];camera=scene.camera
    d=source['glass_dimensions'];ior=source['glass_material']['ior'];cam=root.matrix_world.inverted()@camera.matrix_world.translation
    results=[];deps=bpy.context.evaluated_depsgraph_get()
    for r in regions:
        b=r['band_mesh_bounds_register'];slot=r['physical_slot'];points=[]
        for x in (b[0][0],b[0][1]):
            for step in range(17):
                y=slot['y_min']+(slot['y_max']-slot['y_min'])*step/16
                points.append(Vector((x,y,math.sqrt(1.25**2-y*y))))
        shifts=[]
        for point in points:
            lateral=Vector((point.x-cam.x,point.y-cam.y));distance=lateral.length
            air=cam.z-point.z-d['thickness'];lo,hi=0,math.pi/2-1e-8
            for _ in range(45):
                theta=(lo+hi)/2;inside=math.asin(math.sin(theta)/ior)
                if air*math.tan(theta)+d['thickness']*math.tan(inside)<distance:lo=theta
                else:hi=theta
            theta=(lo+hi)/2;inside=math.asin(math.sin(theta)/ior)
            axis=lateral.normalized() if distance else Vector((0,0))
            front=Vector((cam.x,cam.y))+axis*((cam.z-d['front_z'])*math.tan(theta))
            back=front+axis*(d['thickness']*math.tan(inside))
            if not all(abs(q.x)<d['width']/2 and abs(q.y)<d['height']/2 for q in (front,back)):
                raise ValueError('Refracted band path misses the continuous cover')
            ray=Vector((axis.x*math.sin(theta),axis.y*math.sin(theta),-math.cos(theta)))
            world_air=root.matrix_world@(cam+ray*10);world_point=root.matrix_world@point
            a,bpx=project(scene,camera,[world_point,world_air],config['resolution'])
            shifts.append(math.hypot(a[0]-bpx[0],a[1]-bpx[1]))
        box=r['obb_px'];width=min(math.dist(a,b) for a,b in zip(box,box[1:]+box[:1]))
        ratio=max(shifts)/width
        if ratio>config['validation']['maximum_ideal_glass_shift_fraction_of_band_width']:
            raise ValueError('Ideal glass displacement exceeds annotation inspection tolerance')
        # Independent visibility rays begin just behind the cover and must hit
        # this digit's printed band before a neighbor or mechanical side part.
        for y in (-.20,0,.20):
            point=Vector(((r['band_mesh_bounds_register'][0][0]+r['band_mesh_bounds_register'][0][1])/2,y,math.sqrt(1.25**2-y*y)))
            direction=(point-cam).normalized();origin=cam+direction*((d['back_z']-.001-cam.z)/direction.z)
            world_origin=root.matrix_world@origin;world_direction=(root.matrix_world.to_3x3()@direction).normalized()
            for _ in range(32):
                hit,location,_,_,obj,_=scene.ray_cast(deps,world_origin,world_direction)
                if not hit or not obj.hide_render:break
                # Saved inspection scenes also contain single-wheel masks that
                # are disabled for rendering. Ignore their ray intersections.
                world_origin=location+world_direction*.0001
            if not hit or obj.name!=r['band_object']:raise ValueError(f'Visible band center ray hits {obj.name if hit else "nothing"} instead of {r["band_object"]}')
        results.append({'wheel':r['wheel'],'max_ideal_glass_shift_px':max(shifts),
            'max_shift_fraction_of_band_width':ratio,'optical_paths_inside_cover':True,'visibility_rays_passed':3})
    return results
