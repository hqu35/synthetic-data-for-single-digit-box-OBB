"""Generate a reproducible, varied 100-image 3D VLM evaluation set in Blender."""
import argparse, copy, hashlib, json, math, random, shutil, sys, time, traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import bpy
from digitgen.experiment1_sampling import sample_parameters
from digitgen.experiment1_scene import apply_parameters,fit_register_camera
from digitgen.band_annotations import project_numeral_bands
from digitgen.sampling import wheel_state
from digitgen.export import export_labels,write_json
from digitgen.camera_appearance import process_image, blur_sigma_from_percent
from digitgen.assets import texture_spec, verify_spec

OUT=ROOT/'outputs/VLM_exp'
OUTPUT_INITIALIZED=False
CONFIG=ROOT/'configs/perspective_review.json'
SOURCE=ROOT/'outputs/glass_review/protective_glass_review.blend'
SOURCE_PARAMS=ROOT/'outputs/glass_review/02_glass_neutral_parameters.json'
ROLLING_ATLAS_CONFIG=ROOT/'configs/rolling_numerals_atlas.json'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def plan_item(config, index):
    p=sample_parameters(config,index,0)
    rng=random.Random(p['seed']+721003)
    # Unique across all examples, including leading zeros.
    digit_pool=list(range(100000)); random.Random(20261031).shuffle(digit_pool)
    digits=f'{digit_pool[index-1]:05d}'
    transition=[0.0]*5
    if index%5 != 0:
        transition[index%5]=[0.12,0.25,0.4,0.5,0.65,0.8][(index//5)%6]
        if index%4==0: transition[(index+2)%5]=[0.2,0.5,0.75][(index//4)%3]
    # A range of moderate perspective while maintaining tight framing.
    yaw=rng.choice([-1,1])*rng.uniform(8,15)
    p['camera'].update(yaw_deg=yaw,pitch_deg=rng.uniform(-3,3),roll_deg=0,distance=rng.uniform(7.5,8.0),target_register_area_fraction=.905)
    return {'sample_id':f'{index:06d}','digits':digits,'transitions':transition,'parameters':p}

def setup(item, config, source, width_scale=0.75, atlas_path=None, rolling_geometry=None):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    if rolling_geometry:
        radius_scale=rolling_geometry['wheel_radius_scale']
        window_scale=rolling_geometry['window_height_scale']
        # Shrink each wheel radially around its axle, then move its axle forward
        # to keep the raised printed surface at the existing glass clearance.
        for i in range(5):
            axle=bpy.data.objects[f'wheel_{i}_axle']
            axle.scale.y=radius_scale;axle.scale.z=radius_scale
            axle.location.z=(1-radius_scale)*rolling_geometry['original_band_radius']
        # Scale the window frame's vertical dimensions around its center.
        for obj in bpy.context.scene.objects:
            if obj.name.startswith('front_review_'):
                obj.location.y*=window_scale;obj.scale.y*=window_scale
    if atlas_path is not None:
        atlas=bpy.data.images.load(str(atlas_path),check_existing=True)
        atlas.colorspace_settings.name='Non-Color'
        for i in range(5):
            material=bpy.data.objects[f'wheel_{i}_raised_band'].data.materials[0]
            node=material.node_tree.nodes.get('Cylindrical ink mask')
            if node is None: raise ValueError('Numeral band is missing its cylindrical ink mask')
            node.image=atlas
    # Scale the complete register along the axle: wheel widths, pitch, gaps,
    # frame and glass all stay mechanically aligned. Height and depth stay fixed.
    bpy.data.objects['RegisterHousing'].scale.x=width_scale
    bpy.context.view_layer.update()
    resolved=apply_parameters(config,item['parameters'],source)
    framing=fit_register_camera(config,item['parameters'])
    states=[wheel_state(i,int(d),t) for i,(d,t) in enumerate(zip(item['digits'],item['transitions']))]
    rotation_sign=rolling_geometry.get('rotation_sign',1) if rolling_geometry else 1
    if rotation_sign not in (-1,1):raise ValueError('rotation_sign must be -1 or 1')
    for state in states:
        state['wheel_rotation']*=rotation_sign
        state['rotation_sign']=rotation_sign
        bpy.data.objects[f"wheel_{state['index']}_axle"].rotation_euler.x=state['wheel_rotation']
    bpy.context.view_layer.update()
    scene=bpy.context.scene
    scene.cycles.seed=item['parameters']['seed']%2147483647
    regions=project_numeral_bands(scene,scene.camera,bpy.data.objects['RegisterHousing'],config['resolution'])
    for region in regions:
        for x,y in region['obb_px']:
            if not (0<=x<=config['resolution'][0] and 0<=y<=config['resolution'][1]): raise ValueError('OBB outside image')
    return scene,states,regions,resolved,framing

def main():
    global OUT, OUTPUT_INITIALIZED
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blur-percent', type=float, default=0, help='Gaussian blur strength from 0 to 50')
    parser.add_argument('--wheel-width-scale', type=float, default=0.75, help='Horizontal register scale (default: 0.75)')
    parser.add_argument('--yaw-center',type=float,help='Camera yaw in degrees relative to frontal')
    parser.add_argument('--yaw-spread',type=float,default=2,help='Maximum variation around --yaw-center in degrees')
    parser.add_argument('--blue-light',action='store_true',help='Use blue-tinted scene lights for every image')
    parser.add_argument('--count',type=int,default=100,help='Number of images (1 to 100)')
    parser.add_argument('--seed-base',type=int,default=2026103100,help='Base for unique deterministic image seeds')
    parser.add_argument('--output', default='outputs/VLM_exp', help='New output directory')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    blur_sigma_from_percent(args.blur_percent, (1600,460))
    if not math.isfinite(args.wheel_width_scale) or not 0.5 <= args.wheel_width_scale <= 1:
        raise ValueError('wheel-width-scale must be between 0.5 and 1 inclusive')
    if not 1<=args.count<=100:raise ValueError('count must be between 1 and 100')
    if not math.isfinite(args.yaw_spread) or args.yaw_spread<0:raise ValueError('yaw-spread must be finite and nonnegative')
    if args.yaw_center is not None and (not math.isfinite(args.yaw_center) or abs(args.yaw_center)+args.yaw_spread>45):
        raise ValueError('yaw-center and spread must stay between -45 and 45 degrees')
    OUT=(ROOT/args.output).resolve()
    if OUT.exists() and any(OUT.iterdir()): raise ValueError('Select a new or empty output directory')
    OUTPUT_INITIALIZED=True
    config=json.loads(CONFIG.read_text()); config['count']=args.count;config['seed']=args.seed_base
    config['requested_yaw_center_deg']=args.yaw_center
    config['requested_yaw_spread_deg']=args.yaw_spread if args.yaw_center is not None else None
    config['blue_light']=args.blue_light
    config['blur_percent']=args.blur_percent
    # Match the output aspect ratio to the narrower physical register so that
    # the approved tight-framing constraint remains feasible.
    config['resolution'][0]=round(config['resolution'][0]*args.wheel_width_scale)
    config['wheel_width_scale']=args.wheel_width_scale
    config['camera'].pop('pose_overrides',None)
    source=json.loads(SOURCE_PARAMS.read_text())
    rolling_config=json.loads(ROLLING_ATLAS_CONFIG.read_text())
    atlas=texture_spec(rolling_config)
    verify_spec(atlas)
    config['rolling_geometry']=rolling_config['geometry']
    config['rolling_atlas']=atlas
    plan=[plan_item(config,i) for i in range(1,args.count+1)]
    for item in plan:
        rng=random.Random(item['parameters']['seed']+64039)
        if args.yaw_center is not None:
            item['parameters']['camera']['yaw_deg']=rng.uniform(args.yaw_center-args.yaw_spread,args.yaw_center+args.yaw_spread)
            item['parameters']['camera']['target_register_area_fraction']=.902
        if args.blue_light:
            lighting=item['parameters']['lighting']
            lighting.update(preset='blue_tint',temperature_kelvin=None,
                            temperature_rgb=[rng.uniform(.52,.60),rng.uniform(.74,.82),1.0])
    assert len({x['digits'] for x in plan})==len({x['parameters']['seed'] for x in plan})==args.count
    for d in ('images','labels','metadata'): (OUT/d).mkdir(parents=True,exist_ok=True)
    write_json(OUT/'config.json',config)
    shutil.copy2(__file__,OUT/'generator_snapshot.py')
    (OUT/'README.md').write_text('''# VLM experiment: 100 synthetic register images\n\nThe background run produces 100 PNG images, YOLO OBB label files, and per-image JSON metadata. `plan.json` records all seeds, digit sequences, transition progress, lighting, and requested camera settings before rendering. `status.json` records progress; the launch log is stored next to the output directory.\n\nImages are 1600 x 460, tightly framed around the register. The dataset contains 100 unique seeds and digit sequences; 80 samples contain at least one transitioning digit. Camera pose, perspective, lighting, exposure and mild sensor noise vary. The design retains the same underlying 3D register, typography, and glass, so it does not represent all real-world variation.\n\nClass 0 labels are projected 3D digit-band rectangles, not digit identities; JSON records the underlying digit and transition values. Glass refraction is not fitted to labels. Glass can cause a displacement between projected labels and visible pixels, and mid-transition digits can show a substantial gap. This is a synthetic dataset for later comparison, not a VLM evaluation or evidence of a measured sim-to-real gap.\n''')
    readme=OUT/'README.md'
    readme.write_text(readme.read_text().replace('100',str(args.count)).replace('80 samples',f"{sum(any(t>0 for t in x['transitions']) for x in plan)} samples").replace('1600 x 460',f"{config['resolution'][0]} x {config['resolution'][1]}") + f"\nHorizontal geometry scale: {args.wheel_width_scale}; blur: {args.blur_percent}%; blue lights: {args.blue_light}; yaw center/spread: {args.yaw_center}/{args.yaw_spread} degrees.\n")
    completed=[]; t0=time.time()
    write_json(OUT/'status.json',{'state':'preflighting','completed':0,'total':args.count})
    # Preflight the exact geometry of every requested image before starting production.
    for item in plan:
        rng=random.Random(item['parameters']['seed']+9801)
        for attempt in range(60):
            try:
                setup(item,config,source,args.wheel_width_scale,ROOT/atlas['path'],config['rolling_geometry'])
                item['camera_preflight_attempt']=attempt
                break
            except ValueError as exc:
                if attempt==59: raise RuntimeError(f"No valid camera for {item['sample_id']}: {exc}") from exc
                camera=item['parameters']['camera']
                # Keep the sample seed; vary the pose to avoid clipping.
                camera['yaw_deg']=rng.uniform(args.yaw_center-args.yaw_spread,args.yaw_center+args.yaw_spread) if args.yaw_center is not None else rng.choice([-1,1])*rng.uniform(8,15)
                camera['pitch_deg']=rng.uniform(-3,3)
                camera['distance']=rng.uniform(7.5,8.0)
                camera['target_register_area_fraction']=rng.uniform(.9002,.905)
        print('PREFLIGHT_OK',item['sample_id'],flush=True)
    write_json(OUT/'plan.json',{'count':args.count,'samples':plan})
    print('PREFLIGHT_COMPLETE',args.count,'samples',flush=True)
    write_json(OUT/'status.json',{'state':'rendering','completed':0,'total':args.count})
    for item in plan:
        stem=item['sample_id']; scene,states,regions,resolved,framing=setup(item,config,source,args.wheel_width_scale,ROOT/atlas['path'],config['rolling_geometry'])
        image=OUT/'images'/f'{stem}.png'; label=OUT/'labels'/f'{stem}.txt'
        scene.render.filepath=str(image); bpy.ops.render.render(write_still=True)
        ap=item['parameters']['appearance']
        processing={'camera_white_balance':[1,1,1],'postprocess_color_cast':[1,1,1], 'camera_exposure':0,'contrast':ap['contrast'],'blur_percent':args.blur_percent,'sensor_noise_std':ap['sensor_noise_std'],'noise_seed':ap['noise_seed']}
        process_image(image,image,processing)
        export_labels(label,[r['obb_px'] for r in regions],config['resolution'])
        record={**item,'wheel_width_scale':args.wheel_width_scale,'resolution':config['resolution'],'atlas':atlas,'rolling_geometry':config['rolling_geometry'],'wheel_states':states,'resolved_scene':resolved,'framing':framing,'regions':regions,'camera_matrix_world':list(map(list,scene.camera.matrix_world)),'camera_lens_mm':scene.camera.data.lens,'camera_processing':processing,'image_sha256':sha(image),'label_sha256':sha(label),'source_scene_sha256':sha(SOURCE),'blender_version':bpy.app.version_string,'render_samples':scene.cycles.samples,'annotation_note':'Projected band geometry; refraction not corrected.'}
        write_json(OUT/'metadata'/f'{stem}.json',record);completed.append(stem)
        write_json(OUT/'status.json',{'state':'rendering','completed':len(completed),'total':args.count,'last_completed':stem,'elapsed_seconds':round(time.time()-t0,1)})
        print('VLM_SAMPLE_OK',stem,'seed',item['parameters']['seed'],'digits',item['digits'],flush=True)
    write_json(OUT/'status.json',{'state':'complete','completed':len(completed),'total':args.count,'elapsed_seconds':round(time.time()-t0,1)})
    print('VLM_COMPLETE',args.count,flush=True)

if __name__=='__main__':
    try: main()
    except BaseException as exc:
        if not OUTPUT_INITIALIZED:
            raise
        OUT.mkdir(parents=True,exist_ok=True)
        current={}
        if (OUT/'status.json').exists(): current=json.loads((OUT/'status.json').read_text())
        current.update(state='failed',error=repr(exc),traceback=traceback.format_exc())
        write_json(OUT/'status.json',current)
        traceback.print_exc(); raise
