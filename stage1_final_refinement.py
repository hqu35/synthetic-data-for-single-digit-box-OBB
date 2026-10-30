"""Final Stage 1 fixed pin/typography/ink review; never runs a dataset batch."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import bpy
from mathutils import Vector
from stage1_raised_band import parameters,clear,make_windows,show,verify,render
from stage1_geometry import setup_lights
from digitgen.raised_layout import raised_layout
from digitgen.raised_mechanics import build_raised_register,rebuild_pins
from digitgen.pin_calibration import calibrate_pins
from digitgen.pin_visibility import measure_pins
from digitgen.materials import plastic,graph_report
from digitgen.assets import texture_spec,verify_spec
from digitgen.scene import project_regions
from digitgen.geometry import minimum_rectangle
from digitgen.export import write_json,export_labels,svg_overlay


def configure_scene(c):
    clear();s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU'
    s.cycles.samples=c['samples'];s.cycles.use_denoising=True;s.cycles.seed=0
    s.render.threads_mode='FIXED';s.render.threads=c['threads'];s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8'
    s.view_settings.view_transform='AgX';s.view_settings.exposure=0;s.world.use_nodes=True
    s.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.15,.19,1)
    s.world.node_tree.nodes['Background'].inputs[1].default_value=c['world_strength']
    return s


def change_print(c,p,typography=None,gloss=True):
    sample=copy.deepcopy(p['appearance']);sample['ink_gloss_enabled']=gloss
    spec=texture_spec({'typography':typography or c['typography']});verify_spec(spec)
    image=bpy.data.images.load(str(ROOT/spec['path']),check_existing=True);image.colorspace_settings.name='Non-Color'
    mat=plastic('Inspection printed surface',sample,image)
    for i in range(5):bpy.data.objects[f'wheel_{i}_raised_band'].data.materials[0]=mat
    return mat,spec


def set_state(p,index,digit,progress):
    p['wheels'][index].update({'digit':digit,'transition_progress':progress,'wheel_rotation':(digit+progress)*math.pi/5})
    bpy.data.objects[f'wheel_{index}_axle'].rotation_euler.x=p['wheels'][index]['wheel_rotation']
    bpy.context.view_layer.update()


def rolling_fraction(c,t):
    half=math.asin(c['slot_height']/(2*c['band_radius']))
    height=c['typography']['numeral_height']*c['typography']['glyph_height_scale']*math.pi/5
    def fraction(center):return max(0,min(half,center+height/2)-max(-half,center-height/2))/height
    return {'progress':t,'outgoing_glyph_vertical_extent_visible_fraction':fraction(-t*math.pi/5),
            'incoming_glyph_vertical_extent_visible_fraction':fraction((1-t)*math.pi/5),
            'meaning':'Geometric glyph-span visibility, not a claim about each numeral silhouette ink area.'}


def verify_ink(mat,c):
    nodes=mat.node_tree.nodes;bsdf=nodes['Principled BSDF']
    if bsdf.inputs['Metallic'].default_value!=0 or abs(bsdf.inputs['IOR'].default_value-1.5)>1e-6:
        raise AssertionError('Ink and plastic must remain compatible nonmetallic dielectric surfaces')
    rough=nodes['Ink / substrate roughness'].inputs[2].default_value[0]
    if abs(rough-c['material']['ink_roughness'])>1e-6:raise AssertionError('Ink roughness is not mask-controlled')
    reduced=nodes['Ink / substrate micro bump strength'].inputs[2].default_value[0]
    if reduced>=c['material']['micro_bump_strength']:raise AssertionError('Ink micro bump was not reduced')
    return {'metallic':0,'ior':1.5,'ink_roughness':rough,'plastic_roughness':c['material']['plastic_roughness'],
            'ink_micro_bump_strength':reduced,'specular_ior_level_supported':bool(mat.get('ink_specular_ior_level_supported')),
            'ink_specular_ior_level':c['material']['ink_specular_ior_level'],'no_emission_or_bloom':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',default='configs/stage1_final_refinement.json')
    parser.add_argument('--output',default='outputs/stage1_final_refinement')
    parser.add_argument('--preview',action='store_true',help='Render just the 3/4 pin closeups and row at lower sample count')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    c=json.loads((ROOT/args.config).read_text());c['material']['ink_color']=c['typography']['glyph_ink_color']
    if args.preview:c['samples']=16
    resolved=copy.deepcopy(c);resolved.update(calibrate_pins(c,3));resolved['target_visible_pins']=3
    d=raised_layout(resolved);p=parameters(resolved,d);verify_spec(p['texture'])
    out=(ROOT/args.output).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('Use a new/empty Stage 1 review directory')
    out.mkdir(parents=True,exist_ok=True);scene=configure_scene(resolved)
    build_raised_register(resolved,p,ROOT);z=d['band_radius']+c['aperture_standoff'];make_windows(resolved,p,z)
    ink_checks=verify_ink(bpy.data.objects['wheel_2_raised_band'].data.materials[0],c)
    bpy.context.view_layer.update();checks=verify(resolved,p,d)
    views={};visibility={};cameras={};single=c['views']['single'];row=c['views']['row']
    views['A_three_visible_pins'],cameras['single']=render('A_three_visible_pins',single,resolved,p,z,out,single=True)
    visibility['A_three_visible_pins']=measure_pins(resolved,p,cameras['single'],single['resolution'],[2])
    # Same geometry except pin count/pitch/phase; freeze the exact single camera.
    four=copy.deepcopy(resolved);four.update(calibrate_pins(c,4));four['target_visible_pins']=4
    rebuild_pins(four,d)
    views['B_four_visible_pins'],_=render('B_four_visible_pins',single,four,p,z,out,single=True,camera=cameras['single'])
    visibility['B_four_visible_pins']=measure_pins(four,p,cameras['single'],single['resolution'],[2])
    rebuild_pins(resolved,d)
    views['C_fixed_00054_register'],cameras['row']=render('C_fixed_00054_register',row,resolved,p,z,out)
    visibility['C_fixed_00054_register']=measure_pins(resolved,p,cameras['row'],row['resolution'],list(range(5)))
    boundaries=project_regions(scene,cameras['row'],[w['center_x'] for w in p['wheels']],p['slot_width'],p['slot_height'],z,c['frame_depth'],row['resolution'])
    boxes=[minimum_rectangle(b)[0] for b in boundaries];export_labels(out/'test_slot_obbs.txt',boxes,row['resolution'])
    svg_overlay(out/'C_fixed_00054_register.png',out/'test_slot_obbs.txt',out/'G_slot_obb_overlay.svg',row['resolution'])
    fractions=[]
    if not args.preview:
        # Typography-only comparison: centered 70% band, same shader and camera.
        change_print(c,p,c['previous_typography'])
        views['D_previous_heavy_glyph'],_=render('D_previous_heavy_glyph',single,resolved,p,z,out,single=True,camera=cameras['single'])
        views['D_previous_heavy_glyph']['typography']=c['previous_typography']
        mat,spec=change_print(c,p)
        views['D_revised_regular_glyph'],_=render('D_revised_regular_glyph',single,resolved,p,z,out,single=True,camera=cameras['single'])
        views['D_revised_regular_glyph']['typography']=c['typography']
        # Only the actual axle rotates. Aperture/camera/labels remain fixed.
        original=copy.deepcopy(p['wheels'][2])
        for name,t in [('E_stable_4',0),('E_4_to_5_025',.25),('E_4_to_5_050',.5),('E_4_to_5_075',.75)]:
            set_state(p,2,4,t)
            views[name],_=render(name,single,resolved,p,z,out,single=True,camera=cameras['single'])
            views[name].update({'digit':4,'transition_progress':t})
            visibility[name]=measure_pins(resolved,p,cameras['single'],single['resolution'],[2],require_target=False)
            fractions.append(rolling_fraction(c,t))
        set_state(p,2,original['digit'],original['transition_progress'])
        # Suitable fixed illumination for comparing matte versus smooth ink.
        light=c['ink_inspection_light'];data=bpy.data.lights.new(light['name'],'AREA');data.shape='RECTANGLE'
        data.energy=light['energy'];data.size=light['size'];data.size_y=light['size_y'];data.color=light['color']
        obj=bpy.data.objects.new(light['name'],data);bpy.context.collection.objects.link(obj);obj.location=light['position']
        obj.rotation_euler=(Vector((0,0,c['band_radius']))-obj.location).to_track_quat('-Z','Y').to_euler()
        # Use numeral 4 for both material samples.
        set_state(p,2,4,0)
        change_print(c,p,gloss=False)
        views['F_uniform_matte'],_=render('F_uniform_matte',single,resolved,p,z,out,single=True,camera=cameras['single'])
        views['F_uniform_matte']['ink_gloss_enabled']=False
        mat,_=change_print(c,p,gloss=True)
        views['F_slightly_glossy_ink'],_=render('F_slightly_glossy_ink',single,resolved,p,z,out,single=True,camera=cameras['single'])
        views['F_slightly_glossy_ink']['ink_gloss_enabled']=True
        bpy.data.objects.remove(obj,do_unlink=True);set_state(p,2,original['digit'],original['transition_progress'])
        write_json(out/'ink_shader_nodes.json',graph_report(mat))
    # Self-contained review .blend opens with 00054 and the regular print.
    show(row);setup_lights(c,False);scene.camera=cameras['row']
    scene.render.resolution_x,scene.render.resolution_y=row['resolution']
    for image in bpy.data.images:
        if image.source=='FILE':image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'final_stage1_review.blend'))
    files=[ROOT/'stage1_final_refinement.py',*sorted((ROOT/'digitgen').glob('*.py')),ROOT/'prepare_assets.py']
    report={'stage':'Final Stage 1 refinement; STOP for human approval','training_dataset_generated':False,'randomization':False,
        'config':c,'resolved_three_pin_config':resolved,'four_pin_calibration':calibrate_pins(c,4),
        'layout':d,'parameters':p,'geometry_checks':checks,'ink_shader_checks':ink_checks,'blender_version':bpy.app.version_string,'views':views,'pin_visibility':visibility,
        'rolling_glyph_visibility':fractions,'test_obb_corners_px':boxes,'projected_slot_boundaries_px':boundaries,
        'ink_inspection_light':c['ink_inspection_light'],'source_sha256':hashlib.sha256(b''.join(f.read_bytes() for f in files)).hexdigest(),
        'next_step':'Wait for explicit human approval. No glass, randomized data, diffusion or model training.'}
    write_json(out/'inspection_report.json',report)
    print(json.dumps({'status':'Stage 1 inspection rendered','pin_counts':{key:[r['actually_visible_count'] for r in value] for key,value in visibility.items()},'layout':d},indent=2))


if __name__=='__main__':main()
