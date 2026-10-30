"""Actual cylindrical UV meshes, beveled rims/pins, and solid apertures."""
import math
import bpy
from .materials import basic_material, plastic, graph_report


def bevel(obj,width,segments=3):
    if width:
        mod=obj.modifiers.new('Mechanical edge bevel','BEVEL');mod.width=width;mod.segments=segments


def cylinder(name,radius,width,mat,x=0,parent=None,radial_segments=128,bevel_width=0):
    verts=[(side*width/2,radius*math.sin(j*2*math.pi/radial_segments),radius*math.cos(j*2*math.pi/radial_segments))
           for side in (-1,1) for j in range(radial_segments)]
    faces=[(j,j+radial_segments,(j+1)%radial_segments+radial_segments,(j+1)%radial_segments) for j in range(radial_segments)]
    faces += [tuple(range(radial_segments-1,-1,-1)),tuple(range(radial_segments,2*radial_segments))]
    # Correct cap winding independently; outward normals are -X / +X.
    faces[-2]=tuple(range(radial_segments))
    faces[-1]=tuple(range(2*radial_segments-1,radial_segments-1,-1))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name='Circumference_Axial')
    for j,face in enumerate(mesh.polygons[:radial_segments]):
        for loop,coord in zip(face.loop_indices,[(j/radial_segments+.05,0),(j/radial_segments+.05,1),((j+1)/radial_segments+.05,1),((j+1)/radial_segments+.05,0)]):
            uv.data[loop].uv=coord
        face.use_smooth=True
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    obj.parent=parent;obj.location.x=x;obj.data.materials.append(mat)
    bevel(obj,bevel_width)
    return obj


def block(name,x0,x1,y0,y1,front_z,depth,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=((x0+x1)/2,(y0+y1)/2,front_z-depth/2))
    obj=bpy.context.object;obj.name=name
    obj.scale=(x1-x0,y1-y0,depth)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    return obj


def validate_mechanical_layout(p):
    """Check the full body/rim/pin envelope independently of visible slot gaps."""
    g=p['mechanics']
    if min(p['wheel_radius'],p['wheel_width'],g['rim_width'],g['rim_radius'])<=0:
        raise ValueError('Wheel/rim dimensions must be positive')
    expected=p['wheel_width']+g['rim_width']+(g['pin_length'] if g['pin_count'] else 0)
    if abs(g['assembly_width']-expected)>1e-7 or p['pitch']<expected+g['wheel_axial_clearance']-1e-7:
        raise ValueError('Body/rim/protruding pins exceed available mechanical pitch')
    if g['pin_count']:
        if g['pin_count']!=10*g['pins_per_digit_interval'] or min(g['pin_radius'],g['pin_length'])<=0:
            raise ValueError('Invalid mechanical pin count/dimensions')
        if g['pin_radial_position']+g['pin_radius']>g['rim_radius']:
            raise ValueError('Pin bases must fit on the right rim')
        if 2*g['pin_radius']>=2*g['pin_radial_position']*math.sin(math.pi/g['pin_count']):
            raise ValueError('Pins on the same rim intersect')


def build_register(c,p,root,include_frame=True):
    validate_mechanical_layout(p)
    n,w,h,r,pitch=p['digit_count'],p['slot_width'],p['slot_height'],p['wheel_radius'],p['pitch']
    centers=[(i-(n-1)/2)*pitch for i in range(n)]
    a=p['appearance'];g=p['mechanics'];border=c['geometry']['frame_border']
    z=r+c['geometry']['aperture_standoff'];depth=c['geometry']['frame_depth']
    image=bpy.data.images.load(str(root/p['texture']['path']),check_existing=True)
    image.colorspace_settings.name='Non-Color'
    wheelmat=plastic('Wheel printed plastic',a,image)
    plain=plastic('Wheel end / rim plastic',a)
    rimparams=dict(a)
    rimparams['material_color']=[v*a.get('rim_color_factor',1) for v in a['material_color']]
    rimmat=plastic('Distinct right mechanical rim',rimparams) if a.get('rim_color_factor',1)!=1 else plain
    pinmat=basic_material('Pins satin polymer',tuple(v*a.get('pin_color_factor',.8) for v in a['material_color']),a.get('pin_roughness',.7))
    hubmat=basic_material('Axle satin steel',(.15,.16,.17),.55,.55)
    framemat=basic_material('Frame dark molded polymer',(.045,.047,.042),.75)
    casemat=basic_material('Aged surround',(.42,.40,.33),.8)
    half=((n-1)*pitch+w)/2
    for name,x0,x1,y0,y1,mat in [
        ('top',-half-border,half+border,h/2,h/2+border,framemat),
        ('bottom',-half-border,half+border,-h/2-border,-h/2,framemat),
        ('left',-half-border,-half,-h/2,h/2,framemat),('right',half,half+border,-h/2,h/2,framemat),
        ('surround_top',-30,30,h/2+border,30,casemat),('surround_bottom',-30,30,-30,-h/2-border,casemat),
        ('surround_left',-30,-half-border,-h/2-border,h/2+border,casemat),
        ('surround_right',half+border,30,-h/2-border,h/2+border,casemat)]:
        if include_frame:block('register_frame_'+name,x0,x1,y0,y1,z,depth,mat)
    for i,(left,right) in enumerate(zip(centers,centers[1:])):
        if include_frame:block(f'register_frame_separator_{i}',left+w/2,right-w/2,-h/2,h/2,z,depth,framemat)
    for i,x in enumerate(centers):
        parent=bpy.data.objects.new(f'wheel_{i}_axle',None);bpy.context.collection.objects.link(parent)
        parent.location=(x,0,0);parent.rotation_euler.x=p['wheels'][i]['wheel_rotation']
        body=cylinder(f'wheel_{i}_cylinder',r,p['wheel_width'],wheelmat,parent=parent,
                      radial_segments=g['radial_segments'],bevel_width=g['wheel_bevel_width'])
        # End caps are unprinted, using the same substrate family.
        body.data.materials.append(plain)
        for face in body.data.polygons[-2:]:face.material_index=1
        cylinder(f'wheel_{i}_right_rim',g['rim_radius'],g['rim_width'],rimmat,
                 x=p['wheel_width']/2+g['rim_width']/2,parent=parent,bevel_width=g['rim_width']*.15)
        cylinder(f'wheel_{i}_hub',g['axle_radius']*1.8,p['wheel_width']*.98,pinmat,parent=parent,bevel_width=g['wheel_bevel_width'])
        for j in range(g['pin_count']):
            angle=2*math.pi*j/g['pin_count']
            pin=cylinder(f'wheel_{i}_pin_{j:02d}',g['pin_radius'],g['pin_length'],pinmat,
                         x=p['wheel_width']/2+g['rim_width']+g['pin_length']/2,parent=parent,
                         radial_segments=16,bevel_width=g['pin_bevel_width'])
            pin.location.y=g['pin_radial_position']*math.sin(angle)
            pin.location.z=g['pin_radial_position']*math.cos(angle)
        p['wheels'][i].update({'center_x':x,'red':False,'pin_count':g['pin_count']})
    cylinder('common_stationary_axle',g['axle_radius'],(n-1)*pitch+p['mechanics']['assembly_width']+.2,hubmat)
    p['shader_graph']=graph_report(wheelmat)
    return centers,z,depth
