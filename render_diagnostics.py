"""Native Blender diagnostic suite: exposed mechanics, shader comparisons and UV calibration."""
import argparse
import copy
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import bpy
from mathutils import Vector,Matrix
from digitgen.config import load_config
from digitgen.export import write_json
from digitgen.sampling import sample_parameters,wheel_state
from digitgen.scene import create_scene,project
from digitgen.materials import graph_report
from digitgen.camera_appearance import process_image
from generate import export_sample,code_hash


def neutral(p):
    p['photograph'].update({'preset':'neutral','postprocess_color_cast':[1,1,1],'camera_white_balance':[1,1,1],
                            'camera_exposure':0,'contrast':1,'blur_sigma_px':0,'sensor_noise_std':0,'defocus_enabled':False})


def make_dirs(out):
    for name in ('images','raw_images','labels','metadata','overlays','validation'):(out/name).mkdir(parents=True,exist_ok=True)


def finish_set(out,records,kind):
    write_json(out/'manifest.json',{'samples':records,'rejections':[]})
    write_json(out/'validation/render_summary.json',{'successful_images':len(records),'status':'diagnostic_rendered',
                                                    'kind':kind,'source_sha256':code_hash(),'blender_version':bpy.app.version_string})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='configs/preview.json');parser.add_argument('--output',default='outputs/upgrade_diagnostics')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    c=load_config(ROOT/args.config);c['resolution']=[1024,512];c['render']['samples']=48
    out=(ROOT/args.output).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('Diagnostics output must be new or empty')
    out.mkdir(parents=True,exist_ok=True)
    p=sample_parameters(c,0);neutral(p)
    p['requested_angle_deg']=12
    for i in range(p['digit_count']):p['wheels'][i]=wheel_state(i,(i+1)%10,0)
    p['digit_sequence']=''.join(str(w['digit']) for w in p['wheels'])
    # Identical scene parameters, only substrate preset changes.
    materials=out/'materials';make_dirs(materials);records=[]
    for preset in ('basic','reference_dark_plastic','meter_cream_matte'):
        sample=copy.deepcopy(p);sample['appearance']['material_preset']=preset
        scene,boxes,boundaries=create_scene(c,sample)
        records.append(export_sample(materials,preset,c,sample,boxes,boundaries,scene))
        write_json(materials/'validation'/f'{preset}_nodes.json',sample['shader_graph'])
    finish_set(materials,records,'same geometry/camera/lights; three material presets')
    # An exposed oblique view, with real moving pins/rims and no viewing mask.
    sample=copy.deepcopy(p);sample['appearance']['material_preset']='meter_cream_matte'
    cc=copy.deepcopy(c);cc['resolution']=[1200,720];cc['render']['samples']=64
    scene,_,_=create_scene(cc,sample)
    for obj in scene.objects:
        if obj.name.startswith('register_frame_'):obj.hide_render=True
    camera=scene.camera;target=Vector((0,0,0));camera.location=(9,6,11)
    f=(target-camera.location).normalized();right=f.cross(Vector((0,1,0))).normalized();up=right.cross(f)
    camera.rotation_quaternion=Matrix((right,up,-f)).transposed().to_quaternion()
    camera.data.type='ORTHO';camera.data.ortho_scale=12
    bpy.context.view_layer.update()
    corners=[list(obj.matrix_world@Vector(v)) for obj in scene.objects if obj.type=='MESH' and not obj.hide_render for v in obj.bound_box]
    projected=project(scene,camera,corners,cc['resolution'])
    factor=max(abs(value/cc['resolution'][j]-.5)/.44 for point in projected for j,value in enumerate(point))
    camera.data.ortho_scale*=factor;bpy.context.view_layer.update()
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.08,.10,.13,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.3
    # Inspection-only grazing light makes short axial pins and rim bevels readable.
    light=bpy.data.lights.new('inspection_right_grazing','AREA');light.energy=650;light.size=3
    obj=bpy.data.objects.new('inspection_right_grazing',light);bpy.context.collection.objects.link(obj)
    obj.location=(8,4,3);obj.rotation_euler=(Vector((sample['wheels'][-1]['center_x'],0,0))-obj.location).to_track_quat('-Z','Y').to_euler()
    inspection=out/'inspection';inspection.mkdir()
    scene.render.filepath=str(inspection/'exposed_raw.png');bpy.ops.render.render(write_still=True)
    process_image(inspection/'exposed_raw.png',inspection/'exposed.png',sample['photograph'])
    write_json(inspection/'metadata.json',{'diagnostic_only':True,'config':cc,'parameters':sample,
                'lights':[{'name':o.name,'position':list(o.location),'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size} for o in scene.objects if o.type=='LIGHT'],
                'camera_matrix_world':[list(row) for row in camera.matrix_world],
                'ortho_scale':camera.data.ortho_scale,'source_sha256':code_hash(),
                'note':'Viewing mask hidden; no training labels are assigned to this diagnostic.'})
    for image in bpy.data.images:
        if image.source=='FILE':image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(inspection/'assembly.blend'))
    # A true camera close-up, not a modified assembly, reveals the small 3D pins.
    camera.location=(sample['wheels'][-1]['center_x']+5,1.5,4)
    target=Vector((sample['wheels'][-1]['center_x'],0,0))
    f=(target-camera.location).normalized();right=f.cross(Vector((0,1,0))).normalized();up=right.cross(f)
    camera.rotation_quaternion=Matrix((right,up,-f)).transposed().to_quaternion()
    camera.data.ortho_scale=5.4
    scene.render.resolution_x=scene.render.resolution_y=900
    scene.render.filepath=str(inspection/'pin_detail_raw.png');bpy.ops.render.render(write_still=True)
    process_image(inspection/'pin_detail_raw.png',inspection/'pin_detail.png',sample['photograph'])
    # All ten stable digits are rendered to catch mirrored/reversed/offset UVs.
    calibration=out/'uv_calibration';make_dirs(calibration);records=[]
    for start in (0,5):
        cp=copy.deepcopy(c);cp['digit_counts']={'5':1}
        sample=sample_parameters(cp,0);neutral(sample);sample['requested_angle_deg']=8
        sample['camera'].update({'yaw_deg':0,'pitch_deg':0,'projection':'ORTHO'})
        for i in range(5):sample['wheels'][i]=wheel_state(i,start+i,0)
        sample['digit_sequence']=''.join(str(w['digit']) for w in sample['wheels'])
        scene,boxes,boundaries=create_scene(cp,sample)
        records.append(export_sample(calibration,f'digits_{start}_to_{start+4}',cp,sample,boxes,boundaries,scene))
    finish_set(calibration,records,'all ten stable digits; fixed orthographic frontal UV calibration')
    # Independent photographic transform, while physical material/light stay fixed.
    color=out/'camera_casts';make_dirs(color);records=[]
    for preset,gains in [('neutral',[1,1,1]),('cool_blue',[.86,.97,1.14]),('warm',[1.10,1.01,.9])]:
        sample=copy.deepcopy(p);neutral(sample)
        sample['photograph'].update({'preset':preset,'postprocess_color_cast':gains})
        scene,boxes,boundaries=create_scene(c,sample)
        records.append(export_sample(color,preset,c,sample,boxes,boundaries,scene))
    finish_set(color,records,'same cream material and lights; independent neutral/cool/warm camera gain')
    write_json(out/'suite.json',{'status':'rendered','sets':['materials','uv_calibration','camera_casts'],'inspection':'inspection/exposed.png',
                                'source_sha256':code_hash()})


if __name__=='__main__':main()
