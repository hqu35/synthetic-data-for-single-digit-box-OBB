"""One closed physical cover, native Cycles dielectric, and optical validation."""
import hashlib
import math
import struct
import bpy
import bmesh
from mathutils import Vector
from .mechanics import block,bevel
from .materials import basic_material


def mechanical_signature():
    h=hashlib.sha256()
    for obj in sorted(bpy.context.scene.objects,key=lambda o:o.name):
        if not (obj.name.startswith('wheel_') or obj.name=='common_stationary_axle'):continue
        h.update(obj.name.encode())
        for row in obj.matrix_world:
            h.update(struct.pack('4d',*row))
        if obj.type=='MESH':
            for vertex in obj.data.vertices:h.update(struct.pack('3d',*vertex.co))
            for polygon in obj.data.polygons:
                h.update(struct.pack(f'{len(polygon.vertices)}I',*polygon.vertices))
            for modifier in obj.modifiers:
                h.update(modifier.type.encode())
                if modifier.type=='BEVEL':h.update(struct.pack('di',modifier.width,modifier.segments))
    return h.hexdigest()


def dimensions(config,reference):
    g=config['glass'];p=reference['parameters'];height=p['slot_height']
    units_per_mm=height/g['assumed_clear_aperture_height_mm']
    width=4*p['pitch']+p['slot_width']
    # Highest mechanical radius is the edge collar, not the numeral-band surface.
    highest=reference['config']['edge_rim_radius']
    thickness=g['thickness_mm']*units_per_mm;gap=g['distance_to_wheel_surface_mm']*units_per_mm
    back=highest+gap
    return {'unit_convention':'Assume current 0.74-unit clear aperture height corresponds to 12 mm; this is an explicit configurable scale assumption, not a measurement.',
            'units_per_mm':units_per_mm,'mm_per_unit':1/units_per_mm,
            'width':width+2*g['side_margin_mm']*units_per_mm,
            'height':height+2*g['top_bottom_margin_mm']*units_per_mm,
            'thickness':thickness,'back_z':back,'front_z':back+thickness,
            'highest_mechanical_surface_z':highest,'air_gap_to_mechanics':gap,
            'clear_register_width':width,'clear_register_height':height,
            'side_margin':g['side_margin_mm']*units_per_mm,'vertical_margin':g['top_bottom_margin_mm']*units_per_mm}


def glass_material(config,roughness=None,imperfections=None):
    g=config['glass'];roughness=g['roughness'] if roughness is None else roughness
    imperfections=g['glass_imperfections_enabled'] if imperfections is None else imperfections
    mat=basic_material('Protective cover dielectric',(1,1,1),roughness,0)
    nodes,links=mat.node_tree.nodes,mat.node_tree.links;bsdf=nodes.get('Principled BSDF')
    transmission='Transmission Weight' if 'Transmission Weight' in bsdf.inputs else 'Transmission'
    if transmission not in bsdf.inputs:raise ValueError('Installed Principled shader has no transmission input')
    bsdf.inputs[transmission].default_value=g['transmission_weight'];bsdf.inputs['IOR'].default_value=g['ior']
    bsdf.inputs['Alpha'].default_value=1
    specular='Specular IOR Level' if 'Specular IOR Level' in bsdf.inputs else 'Specular'
    if specular in bsdf.inputs:bsdf.inputs[specular].default_value=g['specular_ior_level']
    if imperfections:
        tex=nodes.new('ShaderNodeTexCoord');noise=nodes.new('ShaderNodeTexNoise');noise.name='Very weak correlated glass microstructure'
        noise.inputs['Scale'].default_value=g['glass_noise_scale'];noise.inputs['Detail'].default_value=2
        links.new(tex.outputs['Object'],noise.inputs['Vector'])
        ramp=nodes.new('ShaderNodeMapRange');ramp.name='Bounded micro roughness'
        ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1
        ramp.inputs['To Min'].default_value=max(0,roughness-g['glass_micro_roughness_strength'])
        ramp.inputs['To Max'].default_value=roughness+g['glass_micro_roughness_strength']
        links.new(noise.outputs['Fac'],ramp.inputs['Value']);links.new(ramp.outputs['Result'],bsdf.inputs['Roughness'])
        bump=nodes.new('ShaderNodeBump');bump.name='Subpixel normal variation'
        bump.inputs['Strength'].default_value=g['glass_normal_noise_strength'];bump.inputs['Distance'].default_value=g['glass_bump_distance_units']
        links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
    return mat,{'shader':'Principled BSDF','transmission_input':transmission,'transmission_weight':g['transmission_weight'],
        'alpha':1,'metallic':0,'ior':g['ior'],'roughness':roughness,'specular_input':specular,
        'specular_ior_level':g['specular_ior_level'],'imperfections_enabled':imperfections,
        'normal_incidence_interface_reflectance':((g['ior']-1)/(g['ior']+1))**2}


def add_cover(config,reference):
    scene=bpy.context.scene;d=dimensions(config,reference)
    root=bpy.data.objects.new('RegisterHousing',None);bpy.context.collection.objects.link(root)
    for obj in list(scene.objects):
        if obj.parent is None and (obj.name.startswith('wheel_') or obj.name.startswith('front_review_') or obj.name=='common_stationary_axle'):
            obj.parent=root
    material,properties=glass_material(config)
    cover=block('Continuous_glass_cover',-d['width']/2,d['width']/2,-d['height']/2,d['height']/2,d['front_z'],d['thickness'],material)
    cover.parent=root;bevel(cover,d['thickness']*config['glass']['edge_bevel_ratio'],3)
    # Narrow external seat, outside the cover's clear surface.
    trim=basic_material('Glass seat polymer',(.045,.05,.047),.65)
    w,h=d['width']/2,d['height']/2;lip=.022
    depth=d['front_z']-(reference['parameters']['wheel_radius']+reference['config']['aperture_standoff'])
    for name,x0,x1,y0,y1 in [('left',-w-lip,-w,-h-lip,h+lip),('right',w,w+lip,-h-lip,h+lip),
                            ('top',-w,w,h,h+lip),('bottom',-w,w,-h-lip,-h)]:
        obj=block('glass_seat_'+name,x0,x1,y0,y1,d['front_z']-.01,depth,trim);obj.parent=root
    bpy.context.view_layer.update()
    evaluated=cover.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
    bm=bmesh.new();bm.from_mesh(mesh)
    if any(not edge.is_manifold for edge in bm.edges):raise AssertionError('Glass cover is not closed/manifold')
    volume=bm.calc_volume(signed=True);bm.free();evaluated.to_mesh_clear()
    if volume<=0:raise AssertionError('Glass has inverted normals or no positive volume')
    d.update({'closed_mesh':'passed','signed_volume':volume,'one_continuous_cover':True,
              'parent':'RegisterHousing','seat_width_units':lip})
    return cover,d,properties


def refracted_projection(point,camera,scene,resolution,d,ior):
    """Exact Snell solution for an ideal flat parallel cover, no alpha shortcut."""
    point=Vector(point);cam=camera.matrix_world.translation
    lateral=Vector((point.x-cam.x,point.y-cam.y));distance=lateral.length
    air=cam.z-point.z-d['thickness']
    if air<=0 or point.z>=d['back_z']:raise ValueError('Optical target must be behind the cover')
    lo,hi=0,math.pi/2-1e-8
    for _ in range(60):
        theta=(lo+hi)/2;inside=math.asin(math.sin(theta)/ior)
        span=air*math.tan(theta)+d['thickness']*math.tan(inside)
        if span<distance:lo=theta
        else:hi=theta
    theta=(lo+hi)/2;inside=math.asin(math.sin(theta)/ior)
    direction=lateral.normalized() if distance else Vector((0,0))
    front_xy=Vector((cam.x,cam.y))+direction*((cam.z-d['front_z'])*math.tan(theta))
    back_xy=front_xy+direction*(d['thickness']*math.tan(inside))
    covered=all(abs(p.x)<d['width']/2 and abs(p.y)<d['height']/2 for p in (front_xy,back_xy))
    ray=Vector((direction.x*math.sin(theta),direction.y*math.sin(theta),-math.cos(theta)))
    projected=__import__('bpy_extras.object_utils',fromlist=['world_to_camera_view']).world_to_camera_view(scene,camera,cam+ray*10)
    return [projected.x*resolution[0],(1-projected.y)*resolution[1]],covered
