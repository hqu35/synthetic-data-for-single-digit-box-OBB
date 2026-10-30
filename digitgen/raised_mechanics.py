"""Two-layer drums: solid recessed base, annular UV band, edge collar and pins."""
import math
import bpy
from .mechanics import cylinder,bevel
from .materials import plastic,basic_material
from .raised_layout import raised_layout


def sleeve(name,inner,outer,width,x,parent,printed,plain,segments=192,bevel_width=0):
    # Four rings, closed inner wall, two real annular shoulders. No overlapping
    # solid cylinders: the inner sleeve surface touches the drum at its radius.
    verts=[(side*width/2,r*math.sin(j*2*math.pi/segments),r*math.cos(j*2*math.pi/segments))
           for r,side in [(outer,-1),(outer,1),(inner,-1),(inner,1)] for j in range(segments)]
    faces=[]
    for j in range(segments):
        k=(j+1)%segments
        faces += [(j,segments+j,segments+k,k),
                  (2*segments+j,2*segments+k,3*segments+k,3*segments+j),
                  (j,k,2*segments+k,2*segments+j),
                  (segments+j,3*segments+j,3*segments+k,segments+k)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    mesh.materials.append(printed);mesh.materials.append(plain)
    uv=mesh.uv_layers.new(name='Circumference_Axial')
    for i,face in enumerate(mesh.polygons):
        j=i//4;kind=i%4;face.material_index=0 if kind==0 else 1
        face.use_smooth=kind in (0,1)
        if kind==0:
            for loop,coord in zip(face.loop_indices,[(j/segments+.05,0),(j/segments+.05,1),((j+1)/segments+.05,1),((j+1)/segments+.05,0)]):uv.data[loop].uv=coord
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    obj.parent=parent;obj.location.x=x;bevel(obj,bevel_width)
    return obj


def build_raised_register(c,p,root):
    d=raised_layout(c)
    image=bpy.data.images.load(str(root/p['texture']['path']),check_existing=True)
    image.colorspace_settings.name='Non-Color'
    printed=plastic('Raised band — unchanged printed cream plastic',p['appearance'],image)
    plain=plastic('Raised band annular shoulders',p['appearance'])
    recessed=dict(p['appearance']);recessed['material_color']=[v*c['material']['rim_color_factor'] for v in recessed['material_color']]
    base_mat=plastic('Recessed drum — existing mechanical plastic tint',recessed)
    pin_mat=basic_material('Pins satin polymer',tuple(v*c['material']['pin_color_factor'] for v in p['appearance']['material_color']),c['material']['pin_roughness'])
    for i,state in enumerate(p['wheels']):
        center=(i-2)*d['pitch'];state['center_x']=center
        parent=bpy.data.objects.new(f'wheel_{i}_axle',None);bpy.context.collection.objects.link(parent)
        parent.location.x=center;parent.rotation_euler.x=state['wheel_rotation']
        cylinder(f'wheel_{i}_base_drum',d['base_radius'],d['base_width'],base_mat,parent=parent,
                 radial_segments=c['radial_segments'],bevel_width=c['base_bevel_width'])
        sleeve(f'wheel_{i}_raised_band',d['base_radius'],d['band_radius'],d['band_width'],d['band_center'],parent,
               printed,plain,c['radial_segments'],c['band_bevel_width'])
        sleeve(f'wheel_{i}_band_edge_rim',d['base_radius'],c['edge_rim_radius'],c['edge_rim_width'],
               d['band_right']+c['edge_rim_width']/2,parent,base_mat,base_mat,c['radial_segments'],.002)
        count=c.get('total_pin_count',10*c.get('pins_per_digit_interval',2))
        phase=math.radians(c.get('pin_phase_offset_degrees',0))
        for j in range(count):
            angle=j*2*math.pi/count+phase
            obj=cylinder(f'wheel_{i}_pin_{j:02d}',d['pin_radius'],d['pin_length'],pin_mat,
                         x=d['pin_center_x'],parent=parent,radial_segments=32,bevel_width=c['pin_bevel_width'])
            obj.location.y=d['pin_radial_position']*math.sin(angle);obj.location.z=d['pin_radial_position']*math.cos(angle)
    axle=basic_material('Common stationary axle',(.15,.16,.17),.55,.55)
    cylinder('common_stationary_axle',c['axle_radius'],4*d['pitch']+d['physical_width']+.18,axle)
    return d


def rebuild_pins(c,d):
    """Change only the physical pin pitch/phase for a matched inspection."""
    previous=[obj for obj in bpy.context.scene.objects if obj.name.startswith('wheel_') and '_pin_' in obj.name]
    material=previous[0].data.materials[0]
    for obj in previous:bpy.data.objects.remove(obj,do_unlink=True)
    for i in range(5):
        parent=bpy.data.objects[f'wheel_{i}_axle']
        for j in range(c['total_pin_count']):
            angle=math.radians(c['pin_phase_offset_degrees']+j*c['pin_pitch_degrees'])
            pin=cylinder(f'wheel_{i}_pin_{j:02d}',d['pin_radius'],d['pin_length'],material,
                         x=d['pin_center_x'],parent=parent,radial_segments=32,bevel_width=c['pin_bevel_width'])
            pin.location.y=d['pin_radial_position']*math.sin(angle);pin.location.z=d['pin_radial_position']*math.cos(angle)
    bpy.context.view_layer.update()
