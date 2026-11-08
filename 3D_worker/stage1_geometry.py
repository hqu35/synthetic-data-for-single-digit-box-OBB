"""STAGE 1 ONLY: fixed mechanical inspection. Never generates training labels/data."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import bpy
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
from digitgen.assets import texture_spec,verify_spec
from digitgen.export import write_json
from digitgen.mechanics import build_register,block,cylinder
from digitgen.materials import basic_material


def fixed_parameters(cfg):
    body,rim,pin=cfg['wheel_width'],cfg['rim_width'],cfg['pin_length']
    envelope=body+rim+pin;pitch=envelope+cfg['wheel_axial_clearance']
    states=[]
    for i,(digit,progress) in enumerate(zip(cfg['digit_sequence'],cfg['transition_progress'])):
        d=int(digit)
        states.append({'index':i,'digit':d,'transition_progress':progress,'wheel_rotation':(d+progress)*2*math.pi/10})
    return {'digit_count':5,'digit_sequence':cfg['digit_sequence'],'wheel_radius':cfg['wheel_radius'],
            'wheel_width':body,'slot_width':cfg['slot_width'],'slot_height':cfg['slot_height'],'pitch':pitch,
            'wheels':states,'appearance':copy.deepcopy(cfg['material']),'texture':texture_spec(cfg),
            'mechanics':{'wheel_bevel_width':cfg['wheel_bevel_width'],'rim_radius':cfg['rim_radius'],
                         'rim_width':rim,'axle_radius':cfg['axle_radius'],'radial_segments':cfg['radial_segments'],
                         'pins_enabled':True,'pins_per_digit_interval':cfg['pins_per_digit_interval'],
                         'pin_count':10*cfg['pins_per_digit_interval'],'pin_radius':cfg['pin_radius'],
                         'pin_length':pin,'pin_radial_position':cfg['pin_radial_position'],
                         'pin_bevel_width':cfg['pin_bevel_width'],'assembly_width':envelope,
                         'wheel_axial_clearance':cfg['wheel_axial_clearance']}}


def front_window(cfg,p,z):
    half=((p['digit_count']-1)*p['pitch']+p['slot_width'])/2
    h=p['slot_height'];b=cfg['frame_border'];d=cfg['frame_depth']
    trim=basic_material('Thin stationary aperture lip',(.045,.055,.058),.7)
    surround=basic_material('Light stationary mask',(.65,.66,.59),.75)
    for name,x0,x1,y0,y1,mat in [
        ('top_lip',-half-b,half+b,h/2,h/2+b,trim),('bottom_lip',-half-b,half+b,-h/2-b,-h/2,trim),
        ('left_lip',-half-b,-half,-h/2,h/2,trim),('right_lip',half,half+b,-h/2,h/2,trim),
        ('surround_top',-8,8,h/2+b,4,surround),('surround_bottom',-8,8,-4,-h/2-b,surround),
        ('surround_left',-8,-half-b,-h/2-b,h/2+b,surround),('surround_right',half+b,8,-h/2-b,h/2+b,surround)]:
        block('front_review_'+name,x0,x1,y0,y1,z,d,mat)
    centers=[w['center_x'] for w in p['wheels']]
    for i,(left,right) in enumerate(zip(centers,centers[1:])):
        block(f'front_review_separator_{i}',left+p['slot_width']/2,right-p['slot_width']/2,-h/2,h/2,z,d,surround)


def setup_lights(cfg,cool=False):
    lights=[]
    for item in cfg['lights']:
        if item['name'] in bpy.data.objects:
            obj=bpy.data.objects[item['name']]
        else:
            data=bpy.data.lights.new(item['name'],'AREA');obj=bpy.data.objects.new(item['name'],data)
            bpy.context.collection.objects.link(obj)
        obj.location=item['position'];obj.data.energy=item['energy'];obj.data.size=item['size']
        obj.data.color=[color*(gain if cool else 1) for color,gain in zip(item['color'],cfg['cool_light_gains'])]
        obj.rotation_euler=(Vector((0,0,.25))-obj.location).to_track_quat('-Z','Y').to_euler()
        lights.append({'name':obj.name,'position':list(obj.location),'energy':obj.data.energy,
                       'size':obj.data.size,'color':list(obj.data.color)})
    return lights


def visibility(view):
    for obj in bpy.context.scene.objects:
        if obj.name.startswith('wheel_'):
            i=int(obj.name.split('_')[1]);obj.hide_render=i not in view['wheels']
        elif obj.name.startswith('front_review_'):obj.hide_render=not view['frame']
        elif obj.name=='common_stationary_axle':obj.hide_render=view['wheels']!=[0,1,2,3,4]


def camera_for(name,view,p,z):
    scene=bpy.context.scene
    data=bpy.data.cameras.new(name);camera=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(camera)
    scene.camera=camera;camera.location=view['position'];camera.rotation_mode='QUATERNION'
    f=(Vector(view['target'])-camera.location).normalized();right=f.cross(Vector((0,1,0))).normalized();up=right.cross(f)
    camera.rotation_quaternion=Matrix((right,up,-f)).transposed().to_quaternion()
    data.type='PERSP';data.lens=50;data.clip_start=.05;data.clip_end=100
    scene.render.resolution_x,scene.render.resolution_y=view['resolution']
    bpy.context.view_layer.update()
    if view['frame']:
        half=((p['digit_count']-1)*p['pitch']+p['slot_width'])/2+.06
        points=[Vector((x,y,z)) for x in (-half,half) for y in (-p['slot_height']/2-.04,p['slot_height']/2+.04)]
    else:
        points=[obj.matrix_world@Vector(v) for obj in scene.objects
                if obj.type=='MESH' and obj.name.startswith('wheel_') and not obj.hide_render for v in obj.bound_box]
    for _ in range(3):
        projected=[world_to_camera_view(scene,camera,point) for point in points]
        factor=max(abs(value-.5)/(.5-view['fit_margin']) for pt in projected for value in (pt.x,pt.y))
        data.lens/=factor;bpy.context.view_layer.update()
    return camera


def verify_geometry(cfg,p):
    scene=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();checks=[];envelopes=[]
    for i,state in enumerate(p['wheels']):
        parent=bpy.data.objects[f'wheel_{i}_axle'];body=bpy.data.objects[f'wheel_{i}_cylinder']
        rim=bpy.data.objects[f'wheel_{i}_right_rim']
        pins=[o for o in scene.objects if o.name.startswith(f'wheel_{i}_pin_')]
        if len(pins)!=20:raise AssertionError('Fixed Stage 1 requires 20 pins per wheel')
        if not all(o.parent==parent for o in pins+[body,rim]):raise AssertionError('Wheel attachments have inconsistent parents')
        if any(abs(math.hypot(v.co.y,v.co.z)-p['wheel_radius'])>1e-5 for v in body.data.vertices):
            raise AssertionError('Body vertices do not lie on a real cylinder')
        if len(body.data.polygons)!=cfg['radial_segments']+2:raise AssertionError('Missing curved circumference/caps')
        if not body.data.uv_layers.get('Circumference_Axial'):raise AssertionError('Missing cylindrical printed UVs')
        if not any(m.type=='BEVEL' and m.width>0 for m in body.modifiers):raise AssertionError('Missing rounded body edges')
        bounds=[]
        for obj in [body,rim,*pins]:
            evaluated=obj.evaluated_get(deps)
            bounds += [evaluated.matrix_world@Vector(v) for v in evaluated.bound_box]
        minimum,maximum=min(v.x for v in bounds),max(v.x for v in bounds)
        envelopes.append([minimum,maximum])
        rim_right=rim.location.x+cfg['rim_width']/2
        for pin in pins:
            if abs(pin.location.x-cfg['pin_length']/2-rim_right)>1e-6:
                raise AssertionError('Pin base must attach to the outer +X rim face')
            if pin.location.x+cfg['pin_length']/2<=rim_right+.1:
                raise AssertionError('Pin does not visibly protrude beyond right rim')
            if abs(math.hypot(pin.location.y,pin.location.z)-cfg['pin_radial_position'])>1e-6:
                raise AssertionError('Pin distribution is not radial')
        # Verify actual parent-driven world motion and restore the exact fixed state.
        local=pins[0].location.copy();before=pins[0].matrix_world.translation.copy()
        old=parent.rotation_euler.x;parent.rotation_euler.x=old+.19;bpy.context.view_layer.update()
        after=pins[0].matrix_world.translation.copy();expected=parent.matrix_world@local
        if (after-before).length<.1 or (after-expected).length>1e-5:raise AssertionError('Pins do not rotate with wheel')
        parent.rotation_euler.x=old;bpy.context.view_layer.update()
        checks.append({'wheel':i,'digit':state['digit'],'transition_progress':state['transition_progress'],
                       'body_radius':p['wheel_radius'],'body_width':p['wheel_width'],'pins':len(pins),
                       'pin_axis':'+X, parallel to wheel axle','pin_protrusion_beyond_rim':cfg['pin_length'],
                       'mesh_curvature':'passed','cylindrical_UV':'passed','parent_rotation':'passed',
                       'world_axial_envelope':[minimum,maximum]})
    gaps=[right[0]-left[1] for left,right in zip(envelopes,envelopes[1:])]
    if any(gap<cfg['wheel_axial_clearance']-1e-5 for gap in gaps):raise AssertionError('Neighboring mechanical envelopes intersect')
    if sum(o.name.endswith('_cylinder') and o.name.startswith('wheel_') for o in scene.objects)!=5:
        raise AssertionError('Expected five wheel body meshes')
    return {'status':'passed','wheel_count':5,'total_pins':100,'adjacent_clearances':gaps,'wheels':checks,
            'scope':'Geometry-only verification; no training samples or OBB exports were generated.'}


def render_view(name,view,cfg,p,z,out,cool=False,camera=None):
    scene=bpy.context.scene;visibility(view);lights=setup_lights(cfg,cool)
    if camera is None:camera=camera_for(name,view,p,z)
    else:
        scene.camera=camera;scene.render.resolution_x,scene.render.resolution_y=view['resolution']
    scene.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True)
    return {'file':name+'.png','camera_matrix_world':[list(row) for row in camera.matrix_world],
            'camera_lens_mm':camera.data.lens,'resolution':view['resolution'],'lights':lights,
            'cool_lighting':cool,'material_color':cfg['material']['material_color'],'visible_wheels':view['wheels'],
            'frame_visible':view['frame']},camera


def debug_geometry():
    orange=basic_material('DEBUG body topology',(1,.24,.025),.5)
    for i in range(5):
        body=bpy.data.objects[f'wheel_{i}_cylinder']
        # Copy the real mesh, retaining its actual topology and wheel transform.
        wire=body.copy();wire.data=body.data.copy();wire.name=f'debug_topology_wheel_{i}'
        bpy.context.collection.objects.link(wire)
        for v in wire.data.vertices:
            v.co.y*=1.003;v.co.z*=1.003
        wire.modifiers.clear();wire.data.materials.clear();wire.data.materials.append(orange)
        mod=wire.modifiers.new('Actual cylinder mesh edges','WIREFRAME');mod.thickness=.004
        wire.parent=body.parent
        axis=cylinder(f'debug_axis_wheel_{i}',.025,1.7,orange,parent=body.parent,radial_segments=16)
        axis['meaning']='Wheel local +X axle; pin axes are parallel'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='configs/stage1_geometry.json')
    parser.add_argument('--output',default='outputs/stage1_geometry')
    parser.add_argument('--debug',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    cfg=json.loads((ROOT/args.config).read_text());p=fixed_parameters(cfg);verify_spec(p['texture'])
    if cfg['stage']!='geometry_review_only' or cfg['digit_sequence']!='00054':raise ValueError('Stage 1 fixed inspection configuration required')
    out=(ROOT/args.output).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('Inspection output must be new or empty')
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU'
    scene.cycles.samples=cfg['samples'];scene.cycles.use_denoising=True;scene.cycles.seed=0
    scene.render.threads_mode='FIXED';scene.render.threads=cfg['threads']
    scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8'
    scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.15,.19,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=cfg['world_strength']
    geometry={'geometry':{key:cfg[key] for key in ('frame_border','frame_depth','aperture_standoff')}}
    _,z,_=build_register(geometry,p,ROOT,include_frame=False)
    front_window(cfg,p,z);bpy.context.view_layer.update()
    checks=verify_geometry(cfg,p);write_json(out/'geometry_checks.json',checks)
    views={};cameras={}
    for name,view in cfg['views'].items():
        views[name],cameras[name]=render_view(name,view,cfg,p,z,out)
    a='A_three_quarter_neutral';c='C_front_neutral'
    for name,base in [('E_three_quarter_cool_blue',a),('F_front_cool_blue',c)]:
        views[name],_=render_view(name,cfg['views'][base],cfg,p,z,out,cool=True,camera=cameras[base])
        if views[name]['camera_matrix_world']!=views[base]['camera_matrix_world'] or views[name]['camera_lens_mm']!=views[base]['camera_lens_mm']:
            raise AssertionError('Neutral/blue comparison changed camera')
    # Save a clean beauty scene before adding optional debug meshes.
    visibility(cfg['views'][a]);setup_lights(cfg,False);scene.camera=cameras[a]
    scene.render.resolution_x,scene.render.resolution_y=cfg['views'][a]['resolution']
    for image in bpy.data.images:
        if image.source=='FILE':image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'stage1_assembly.blend'))
    inventory=[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,
                'local_location':list(o.location),'local_rotation_euler':list(o.rotation_euler),
                'mesh_vertices':len(o.data.vertices) if o.type=='MESH' else None} for o in scene.objects]
    if args.debug:
        debug_geometry()
        views['G_topology_debug'],_=render_view('G_topology_debug',cfg['views'][a],cfg,p,z,out,camera=cameras[a])
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'stage1_debug.blend'))
    files=[ROOT/'stage1_geometry.py',ROOT/'digitgen/mechanics.py',ROOT/'digitgen/materials.py']
    report={'stage':'Stage 1 only; STOP for human geometry review','training_dataset_generated':False,
            'config':cfg,'parameters':p,'geometry_checks':checks,'views':views,'objects':inventory,
            'blender_version':bpy.app.version_string,'source_sha256':hashlib.sha256(b''.join(f.read_bytes() for f in files)).hexdigest(),
            'reference_status':'Provided 00054 cool register crop inspected; principal exposed mechanical photo not available by local path.',
            'next_step':'Wait for explicit human approval before Stage 2. No automatic training render follows.'}
    write_json(out/'inspection_report.json',report)
    print(json.dumps({'status':'Stage 1 complete; awaiting geometry review','output':str(out),'geometry':checks['status'],'views':list(views)},indent=2))


if __name__=='__main__':main()
