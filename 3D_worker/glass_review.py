"""Fixed glass-window review over the approved mechanical scene, not a dataset."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import bpy
from mathutils import Vector,Matrix
from digitgen.glass import add_cover,glass_material,mechanical_signature,refracted_projection
from digitgen.geometry import aperture_corners,convex_intersection,minimum_rectangle,area
from digitgen.scene import project,project_regions
from digitgen.export import write_json,export_labels,svg_overlay
from stage1_raised_band import show
from stage1_geometry import setup_lights


def add_reflections(c,cool=False):
    result=[]
    for item in c['reflections']:
        if item['name'] in bpy.data.objects:obj=bpy.data.objects[item['name']]
        else:
            data=bpy.data.lights.new(item['name'],'AREA');obj=bpy.data.objects.new(item['name'],data);bpy.context.collection.objects.link(obj)
        obj.location=item['position'];obj.data.energy=item['energy'];obj.data.shape='RECTANGLE'
        obj.data.size=item['size_x'];obj.data.size_y=item['size_y']
        gains=(.62,.83,1) if cool else (1,1,1)
        obj.data.color=[value*gain for value,gain in zip(item['color'],gains)]
        forward=(Vector(item['target'])-obj.location).normalized()
        right=forward.cross(Vector((0,1,0))).normalized();up=right.cross(forward)
        obj.rotation_euler=Matrix((right,up,-forward)).transposed().to_euler()
        result.append({'name':obj.name,'position':list(obj.location),'quaternion':list(obj.rotation_euler.to_quaternion()),
                       'energy':obj.data.energy,'size_x':obj.data.size,'size_y':obj.data.size_y,'color':list(obj.data.color)})
    return result


def optical_check(c,reference,d,camera,resolution):
    scene=bpy.context.scene;p=reference['parameters'];cfg=reference['config'];records=[]
    for wheel in p['wheels']:
        x=wheel['center_x'];direct=[];apparent=[];all_covered=True;shifts=[]
        for z in [p['wheel_radius']+cfg['aperture_standoff'],p['wheel_radius']+cfg['aperture_standoff']-cfg['frame_depth']]:
            corners=aperture_corners(x,p['slot_width'],p['slot_height'],z)
            # Refraction through a parallel slab is not a projective homography:
            # sample each straight world-space edge rather than assume that its
            # apparent image is exactly the corner-to-corner chord.
            points=[tuple(a[j]+(b[j]-a[j])*step/24 for j in range(3))
                    for a,b in zip(corners,corners[1:]+corners[:1]) for step in range(24)]
            plain=project(scene,camera,points,resolution);bent=[]
            for point,a in zip(points,plain):
                b,covered=refracted_projection(point,camera,scene,resolution,d,c['glass']['ior'])
                bent.append(b);all_covered=all_covered and covered;shifts.append((Vector(a)-Vector(b)).length)
            direct.append(plain);apparent.append(bent)
        original=convex_intersection(*direct);refracted=convex_intersection(*apparent)
        box,_=minimum_rectangle(original);bent_box,_=minimum_rectangle(refracted)
        intersection=area(convex_intersection(box,bent_box));iou=intersection/(area(box)+area(bent_box)-intersection)
        slot_width_px=(Vector(box[1])-Vector(box[0])).length
        if not all_covered:raise AssertionError(f'Cover does not span the full refracted aperture for wheel {wheel["index"]}')
        records.append({'wheel':wheel['index'],'original_obb_px':box,'apparent_refracted_obb_px':bent_box,
                        'max_boundary_shift_px':max(shifts),'shift_fraction_of_slot_width':max(shifts)/slot_width_px,
                        'obb_iou':iou,'all_optical_paths_inside_single_cover':all_covered,
                        'boundary_samples_per_plane':len(points),
                        'optical_model':'Snell solution for an ideal plane-parallel world-Z slab; sampled aperture edges. Bevel/micro-normal stochastic effects are excluded and require rendered-image inspection.'})
    return records


def camera_oblique(c,d):
    view=c['oblique_camera'];data=bpy.data.cameras.new('Glass oblique camera');camera=bpy.data.objects.new('Glass oblique camera',data)
    bpy.context.collection.objects.link(camera);camera.location=view['position'];camera.rotation_mode='QUATERNION'
    forward=(Vector(view['target'])-camera.location).normalized();right=forward.cross(Vector((0,1,0))).normalized();up=right.cross(forward)
    camera.rotation_quaternion=Matrix((right,up,-forward)).transposed().to_quaternion();data.lens=50
    scene=bpy.context.scene;scene.camera=camera;scene.render.resolution_x,scene.render.resolution_y=view['resolution']
    points=[Vector((x,y,z)) for x in (-d['width']/2-.025,d['width']/2+.025) for y in (-d['height']/2-.025,d['height']/2+.025) for z in (d['back_z'],d['front_z'])]
    for _ in range(3):
        bpy.context.view_layer.update();pixels=project(scene,camera,points,view['resolution'])
        factor=max(abs(value/view['resolution'][j]-.5)/.43 for pt in pixels for j,value in enumerate(pt))
        data.lens/=factor
    bpy.context.view_layer.update();return camera


def maybe_sensor_noise(path,c):
    if not c['sensor_noise']['enabled']:return
    from digitgen.camera_appearance import process_image
    params={'camera_white_balance':[1,1,1],'postprocess_color_cast':[1,1,1],'camera_exposure':0,'contrast':1,
            'blur_sigma_px':0,'sensor_noise_std':c['sensor_noise']['linear_rgb_std'],'noise_seed':c['sensor_noise']['seed']}
    process_image(path,path,params)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',default='configs/glass_review.json')
    parser.add_argument('--output',default='outputs/glass_review');parser.add_argument('--preview',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    c=json.loads((ROOT/args.config).read_text());reference=json.loads((ROOT/c['source_report']).read_text())
    out=(ROOT/args.output).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('Choose a new/empty independent glass review directory')
    out.mkdir(parents=True,exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(ROOT/c['source_scene']))
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16 if args.preview else c['samples']
    scene.cycles.use_denoising=True;scene.cycles.seed=c['seed'];scene.render.threads_mode='FIXED';scene.render.threads=c['threads']
    scene.cycles.max_bounces=16;scene.cycles.transmission_bounces=12;scene.cycles.glossy_bounces=8
    scene.cycles.caustics_refractive=True;scene.cycles.caustics_reflective=True
    show(reference['config']['views']['row']);bpy.context.view_layer.update();before=mechanical_signature()
    cover,d,material_info=add_cover(c,reference);after=mechanical_signature()
    if before!=after:raise AssertionError('Adding the glass changed approved wheel geometry/transforms')
    front=bpy.data.objects['C_fixed_00054_register'];oblique=camera_oblique(c,d)
    front_resolution=reference['config']['views']['row']['resolution'];front_reference=optical_check(c,reference,d,front,front_resolution)
    oblique_reference=optical_check(c,reference,d,oblique,c['oblique_camera']['resolution'])
    if max(r['max_boundary_shift_px'] for r in front_reference)>c['validation']['maximum_front_shift_pixels']:
        raise AssertionError('Front apparent-refraction label shift exceeds configured review tolerance')
    oblique_valid=max(r['shift_fraction_of_slot_width'] for r in oblique_reference)<=c['validation']['maximum_oblique_shift_fraction_of_slot_width']
    views={}
    cases=[('01_no_glass_baseline',False,.035,False,False,front,front_resolution),
           ('02_glass_neutral',True,.035,False,False,front,front_resolution),
           ('03_glass_cool_blue',True,.035,False,True,front,front_resolution),
           ('04_glass_oblique',True,.035,False,False,oblique,c['oblique_camera']['resolution'])]
    if not args.preview:
        cases += [('05_roughness_0015',True,.015,False,False,front,front_resolution),
                  ('06_roughness_0070',True,.070,False,False,front,front_resolution),
                  ('07_subtle_microstructure',True,.035,True,False,front,front_resolution)]
    for name,enabled,roughness,imperfect,cool,camera,resolution in cases:
        cover.hide_render=not enabled;mat,properties=glass_material(c,roughness,imperfect);cover.data.materials[0]=mat
        lights=setup_lights(reference['config'],cool);lights+=add_reflections(c,cool)
        scene.camera=camera;scene.render.resolution_x,scene.render.resolution_y=resolution;bpy.context.view_layer.update()
        if mechanical_signature()!=before:raise AssertionError('Review variant changed mechanical geometry')
        scene.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True);maybe_sensor_noise(out/f'{name}.png',c)
        optical=oblique_reference if camera==oblique else front_reference
        boxes=[r['original_obb_px'] for r in optical]
        export_labels(out/f'{name}_slot_obbs.txt',boxes,resolution)
        svg_overlay(out/f'{name}.png',out/f'{name}_slot_obbs.txt',out/f'{name}_overlay.svg',resolution)
        info={'sample_id':name,'seed':c['seed'],'complete_glass_config':c,'approved_reference_config':reference['config'],
              'approved_wheel_states':reference['parameters']['wheels'],'source_scene_sha256':hashlib.sha256((ROOT/c['source_scene']).read_bytes()).hexdigest(),
              'camera_world_matrix':[list(row) for row in camera.matrix_world],'camera_lens_mm':camera.data.lens,
              'resolution':resolution,'lights':lights,'glass_enabled':enabled,'glass_material':properties,'glass_dimensions':d,
              'mechanical_signature':before,'source_stable_atlas':reference['parameters']['texture'],
              'sensor_noise':c['sensor_noise'],'optical_label_check':optical if enabled else [],
              'ground_truth_policy':'Original projected physical-slot OBBs retained; refracted boxes are diagnostics only, never silent label replacements.',
              'oblique_reuse_tolerance_passed':oblique_valid if camera==oblique else None}
        views[name]=info;write_json(out/f'{name}_parameters.json',info);print('GLASS_REVIEW_OK',name,flush=True)
    cover.hide_render=False;cover.data.materials[0]=glass_material(c)[0];setup_lights(reference['config'],False);add_reflections(c)
    scene.camera=front;scene.render.resolution_x,scene.render.resolution_y=front_resolution
    for image in bpy.data.images:
        if image.source=='FILE' and image.packed_file is None:image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'protective_glass_review.blend'))
    report={'status':'Fixed glass review rendered; STOP for human approval','training_dataset_generated':False,
            'config':c,'blender_version':bpy.app.version_string,'glass_dimensions':d,'material':material_info,
            'mechanical_geometry_unchanged':before==after,'mechanical_signature':before,'views':views,
            'front_optical_check':front_reference,'oblique_optical_check':oblique_reference,'oblique_tolerance_passed':oblique_valid,
            'source_glass_implementation_sha256':hashlib.sha256((ROOT/'digitgen/glass.py').read_bytes()+(ROOT/'glass_review.py').read_bytes()).hexdigest(),
            'scope':'No font substitution, atlas spacing changes, random dataset, diffusion or model training. Glass/font review only.'}
    write_json(out/'inspection_report.json',report)
    print(json.dumps({'output':str(out),'front_max_shift_px':max(r['max_boundary_shift_px'] for r in front_reference),
                      'oblique_max_shift_px':max(r['max_boundary_shift_px'] for r in oblique_reference),
                      'oblique_tolerance_passed':oblique_valid,'mechanical_geometry_unchanged':True},indent=2))


if __name__=='__main__':main()
