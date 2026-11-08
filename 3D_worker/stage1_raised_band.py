"""Fixed raised-band geometry review ONLY. One five-slot diagnostic OBB overlay."""
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
import bmesh
from mathutils import Vector
from stage1_geometry import setup_lights,visibility,camera_for,front_window,fixed_parameters
from digitgen.assets import texture_spec,verify_spec
from digitgen.raised_layout import raised_layout
from digitgen.raised_mechanics import build_raised_register
from digitgen.mechanics import build_register
from digitgen.geometry import minimum_rectangle,area
from digitgen.scene import project_regions
from digitgen.export import write_json,export_labels,svg_overlay


def parameters(c,d):
    states=[{'index':i,'digit':int(digit),'transition_progress':progress,
             'wheel_rotation':(int(digit)+progress)*2*math.pi/10,'center_x':(i-2)*d['pitch']}
            for i,(digit,progress) in enumerate(zip(c['digit_sequence'],c['transition_progress']))]
    return {'digit_count':5,'digit_sequence':c['digit_sequence'],'wheels':states,
            'appearance':copy.deepcopy(c['material']),'texture':texture_spec(c),'wheel_radius':d['band_radius'],
            'slot_width':d['slot_width'],'slot_height':c['slot_height'],'pitch':d['pitch']}


def clear():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)


def make_windows(c,p,z):
    for kind in ('single','row'):
        before=set(bpy.data.objects)
        fp=copy.deepcopy(p)
        if kind=='single':fp['digit_count']=1;fp['wheels']=[p['wheels'][2]]
        front_window(c,fp,z)
        for obj in set(bpy.data.objects)-before:obj.name=obj.name.replace('front_review_',f'front_review_{kind}_',1)


def show(view,single=False):
    visibility(view)
    for obj in bpy.context.scene.objects:
        if obj.name.startswith('front_review_'):
            obj.hide_render=not view['frame'] or not obj.name.startswith('front_review_single_' if single else 'front_review_row_')


def verify(c,p,d):
    scene=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get();envelopes=[];records=[]
    for i in range(5):
        parent=bpy.data.objects[f'wheel_{i}_axle'];base=bpy.data.objects[f'wheel_{i}_base_drum']
        band=bpy.data.objects[f'wheel_{i}_raised_band'];rim=bpy.data.objects[f'wheel_{i}_band_edge_rim']
        pins=[o for o in scene.objects if o.name.startswith(f'wheel_{i}_pin_')]
        if len(pins)!=c.get('total_pin_count',10*c.get('pins_per_digit_interval',2)):raise AssertionError('Incorrect fixed pin count')
        for obj in (band,rim):
            bm=bmesh.new();bm.from_mesh(obj.data)
            if any(not edge.is_manifold for edge in bm.edges):raise AssertionError('Open annular sleeve or missing shoulder')
            volume=bm.calc_volume(signed=True);bm.free()
            if volume<=0:raise AssertionError('Annular sleeve has inverted normals or degenerate volume')
        if band.parent!=parent or any(pin.parent!=parent for pin in pins):raise AssertionError('Band and pins must share axle parent')
        radii={round(math.hypot(v.co.y,v.co.z),5) for v in band.data.vertices}
        if radii!={round(d['base_radius'],5),round(d['band_radius'],5)}:raise AssertionError('Band is not a true annular raised cylinder')
        points=[]
        for obj in [base,band,rim,*pins]:
            obj=obj.evaluated_get(deps);points += [obj.matrix_world@Vector(v) for v in obj.bound_box]
        envelopes.append([min(v.x for v in points),max(v.x for v in points)])
        for pin in pins:
            if abs(pin.location.x-d['pin_length']/2-d['pin_root_x'])>1e-6:raise AssertionError('Pin root detached from band-edge collar')
            if pin.location.x+d['pin_length']/2>d['slot_width']/2+1e-6:raise AssertionError('Pin crosses its slot boundary')
        before=pins[0].matrix_world.translation.copy();old=parent.rotation_euler.x
        parent.rotation_euler.x=old+.17;bpy.context.view_layer.update()
        if (pins[0].matrix_world.translation-before).length<.1:raise AssertionError('Pin does not rotate with band')
        parent.rotation_euler.x=old;bpy.context.view_layer.update()
        records.append({'wheel':i,'annular_band_manifold':True,'band_and_pin_parenting':'passed','pin_count':len(pins)})
    gaps=[right[0]-left[1] for left,right in zip(envelopes,envelopes[1:])]
    if min(gaps)<c['minimum_clearance']-1e-6:raise AssertionError('Adjacent wheel assemblies intersect')
    return {'status':'passed','actual_values':d,'evaluated_clearances':gaps,'wheels':records,
            'contact_semantics':'Base/band and base/rim meet at a shared radial interface; band/rim and rim/pin bases meet at axial faces. No unintended interpenetration.'}


def front_pin_test(p,camera):
    scene=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get()
    pin=bpy.data.objects['wheel_2_pin_00'];target=pin.matrix_world.translation
    hit,position,normal,face,obj,matrix=scene.ray_cast(deps,camera.location,(target-camera.location).normalized())
    if not hit or obj.name!=pin.name:raise AssertionError(f'Front view hides band-edge pin: first hit {obj.name if hit else None}')
    return {'status':'passed','camera_ray_first_hit':obj.name,'world_hit':list(position),
            'meaning':'An actual pin shaft is directly visible inside the near-frontal slot, ahead of the recessed drum.'}


def render(name,view,c,p,z,out,single=False,camera=None,cool=False):
    show(view,single)
    fitp=copy.deepcopy(p)
    if single:fitp['digit_count']=1;fitp['wheels']=[p['wheels'][2]]
    scene=bpy.context.scene;lights=setup_lights(c,cool)
    camera=camera or camera_for(name,view,fitp,z)
    scene.camera=camera;scene.render.resolution_x,scene.render.resolution_y=view['resolution']
    scene.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True)
    return {'file':name+'.png','camera_matrix_world':[list(row) for row in camera.matrix_world],
            'camera_lens_mm':camera.data.lens,'resolution':view['resolution'],'lights':lights,
            'material':copy.deepcopy(p['appearance']),'visible_wheels':view['wheels']},camera


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',default='configs/stage1_raised_band.json')
    parser.add_argument('--output',default='outputs/stage1_raised_band')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    c=json.loads((ROOT/args.config).read_text());d=raised_layout(c);p=parameters(c,d);verify_spec(p['texture'])
    if c['digit_sequence']!='00054' or c['transition_progress']!=[0,0,0,0,.05]:raise ValueError('Fixed Stage 1 reference states required')
    out=(ROOT/args.output).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('Use a new or empty review output directory')
    out.mkdir(parents=True,exist_ok=True);clear()
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU'
    scene.cycles.samples=c['samples'];scene.cycles.use_denoising=True;scene.cycles.seed=0
    scene.render.threads_mode='FIXED';scene.render.threads=c['threads'];scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8'
    scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
    scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.15,.19,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=c['world_strength']
    build_raised_register(c,p,ROOT);z=d['band_radius']+c['aperture_standoff']
    make_windows(c,p,z);bpy.context.view_layer.update();checks=verify(c,p,d)
    views={};cameras={}
    # Explode one real assembly only for the diagnostic, then restore exact mounting.
    offsets={}
    for obj in scene.objects:
        if obj.type=='MESH' and obj.name.startswith('wheel_2_'):
            offsets[obj.name]=obj.location.x
            obj.location.x+=(-.95 if 'base_drum' in obj.name else .05 if 'raised_band' in obj.name else .9)
    views['A_exploded'],cameras['A_exploded']=render('A_exploded',c['views']['A_exploded'],c,p,z,out)
    for name,x in offsets.items():bpy.data.objects[name].location.x=x
    bpy.context.view_layer.update()
    for name in ('B_single_digit_front','C_two_wheel','D_five_wheel_front','E_three_quarter'):
        views[name],cameras[name]=render(name,c['views'][name],c,p,z,out,single=name.startswith('B_'))
        if name.startswith('B_'):checks['near_frontal_pin_visibility']=front_pin_test(p,cameras[name])
    # Exactly one geometry-review OBB per physical slot; no training angle sampling.
    show(c['views']['D_five_wheel_front']);scene.camera=cameras['D_five_wheel_front']
    resolution=c['views']['D_five_wheel_front']['resolution']
    scene.render.resolution_x,scene.render.resolution_y=resolution
    boundaries=project_regions(scene,scene.camera,[w['center_x'] for w in p['wheels']],p['slot_width'],p['slot_height'],z,c['frame_depth'],resolution)
    boxes=[minimum_rectangle(boundary)[0] for boundary in boundaries]
    for box in boxes:
        if area(box)<=0 or any(not(0<=x<=resolution[0] and 0<=y<=resolution[1]) for x,y in box):raise AssertionError('Invalid diagnostic slot OBB')
    export_labels(out/'test_slot_obbs.txt',boxes,resolution)
    svg_overlay(out/'D_five_wheel_front.png',out/'test_slot_obbs.txt',out/'D_front_test_obb_overlay.svg',resolution)
    # Include a supplemental cool front using exactly the same physical scene/camera.
    views['D_front_cool'],_=render('D_front_cool',c['views']['D_five_wheel_front'],c,p,z,out,camera=cameras['D_five_wheel_front'],cool=True)
    # Save the assembled review scene and a front-view ray visibility proof.
    show(c['views']['E_three_quarter']);setup_lights(c,False);scene.camera=cameras['E_three_quarter']
    scene.render.resolution_x,scene.render.resolution_y=c['views']['E_three_quarter']['resolution']
    for image in bpy.data.images:
        if image.source=='FILE':image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'raised_band_assembly.blend'))
    # Before/after: reconstruct previous geometry, but freeze the NEW front
    # camera matrix, lens, render settings, font, plastic and light setup.
    camera_matrix=cameras['B_single_digit_front'].matrix_world.copy();lens=cameras['B_single_digit_front'].data.lens
    old=json.loads((ROOT/c['previous_config']).read_text())
    # Use identical font/raster settings on both sides of the comparison; the
    # high-resolution mask is solely to avoid pixelated inspection close-ups.
    old['typography']=copy.deepcopy(c['typography']);op=fixed_parameters(old)
    clear();geometry={'geometry':{key:old[key] for key in ('frame_border','frame_depth','aperture_standoff')}}
    build_register(geometry,op,ROOT,include_frame=False);oz=old['wheel_radius']+old['aperture_standoff']
    make_windows(old,op,oz);view=c['views']['B_single_digit_front'];show(view,True);setup_lights(c,False)
    data=bpy.data.cameras.new('Frozen comparison camera');camera=bpy.data.objects.new('Frozen comparison camera',data)
    bpy.context.collection.objects.link(camera);camera.matrix_world=camera_matrix;data.lens=lens
    views['F_before_single_front'],_=render('F_before_single_front',view,c,op,oz,out,single=True,camera=camera)
    if views['F_before_single_front']['camera_matrix_world']!=views['B_single_digit_front']['camera_matrix_world']:
        raise AssertionError('Before/after camera conditions changed')
    write_json(out/'geometry_checks.json',checks)
    sources=[ROOT/'stage1_raised_band.py',ROOT/'digitgen/raised_layout.py',ROOT/'digitgen/raised_mechanics.py',ROOT/'digitgen/mechanics.py',ROOT/'digitgen/materials.py']
    write_json(out/'inspection_report.json',{'stage':'Stage 1 raised-band revision; STOP for human approval',
        'randomization':False,'training_dataset_generated':False,'config':c,'parameters':p,'layout':d,
        'checks':checks,'views':views,'test_obb_corners_px':boxes,'projected_slot_boundaries_px':boundaries,
        'annotation_semantics':'One physical slot aperture, including its raised numeral band and visible recessed/edge-mechanism regions. Not tight glyph or band-only boxes.',
        'source_sha256':hashlib.sha256(b''.join(f.read_bytes() for f in sources)).hexdigest(),
        'next_step':'Wait for explicit approval. No glass, new material system, random dataset or Stage 2 work follows.'})
    print(json.dumps({'status':'geometry review rendered; awaiting approval','values':d,'front_pin_visibility':checks['near_frontal_pin_visibility']},indent=2))


if __name__=='__main__':main()
