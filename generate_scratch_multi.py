"""Render 20 varied 3D register images with glass scratches."""
import copy,importlib.util,json,math,random,shutil,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import bpy
import generate_vlm_exp as worker
from digitgen.assets import texture_spec,verify_spec
from digitgen.export import export_labels,write_json

OUT=ROOT/'outputs/scratch_multi_version'
LIGHTS={'blue':[.55,.75,1.0],'white':[1.0,1.0,1.0],
        'natural':[1.0,.97,.92],'pale_blue':[.86,.93,1.0],
        'vintage_beige':[1.0,.93,.83]}
SCRATCH={'heavy':((75,110),(.48,.65)), 'medium':((35,55),(.28,.42)), 'light':((8,18),(.12,.24))}

def scene_config():
    c=json.loads(worker.CONFIG.read_text());c['count']=100;c['seed']=2026103127
    c['camera'].pop('pose_overrides',None);c['resolution']=[1200,460]
    return c

def make_plan(c):
    theta_bins=[-34,-30,-26,-22,-18,-14,-10,-7,-4,-1,2,5,8,11,15,19,23,27,31,34]
    order=list(range(20));random.Random(93741).shuffle(order)
    scratches=['heavy']*12+['medium']*6+['light']*2;random.Random(71289).shuffle(scratches)
    items=[]
    for i in range(1,21):
        item=worker.plan_item(c,i);p=item['parameters'];rng=random.Random(p['seed']+240731)
        item['digits']=''.join(map(str,rng.sample(range(10),5)))
        item['transitions']=[0.0]*5
        if i%4:
            item['transitions'][rng.randrange(5)]=round(rng.uniform(.12,.78),4)
        if i%6==0:item['transitions'][rng.randrange(5)]=round(rng.uniform(.12,.78),4)
        theta=theta_bins[order[i-1]]+rng.uniform(-.7,.7);yaw=rng.uniform(-8,8)
        p['camera'].update(pitch_deg=theta,yaw_deg=yaw,roll_deg=0,distance=rng.uniform(7.5,8.0),target_register_area_fraction=.9005)
        category=list(LIGHTS)[(i-1)%5];base=LIGHTS[category]
        # Every non-blue palette is intentionally restrained. Values are RGB
        # light multipliers, not calibrated Kelvin temperatures.
        gains=[min(1.0,max(0,v*rng.uniform(.985,1.015))) for v in base]
        p['lighting'].update(preset=category,temperature_kelvin=None,temperature_rgb=gains)
        level=scratches[i-1];count,amplitude=SCRATCH[level]
        item['scratch']={'name':level,'scratch_count':rng.randint(*count),'scratch_strength':rng.uniform(*amplitude),
                         'noise_strength':rng.uniform(.1,.3),'seed':p['seed']+343}
        item['light_style']=category;item['theta_deg']=theta;item['yaw_deg']=yaw
        items.append(item)
    assert len({x['digits'] for x in items})==20
    assert all(len(set(x['digits']))==5 and abs(x['theta_deg'])<40 for x in items)
    assert set(''.join(x['digits'] for x in items))==set('0123456789')
    return items

def main():
    if OUT.exists():raise ValueError(f'Output already exists: {OUT}')
    OUT.mkdir(parents=True)
    for name in ('images','labels','metadata'):(OUT/name).mkdir()
    shutil.copy2(__file__,OUT/'generator_snapshot.py')
    config=scene_config();source=json.loads(worker.SOURCE_PARAMS.read_text());rolling=json.loads(worker.ROLLING_ATLAS_CONFIG.read_text());atlas=texture_spec(rolling);verify_spec(atlas)
    source_path=ROOT/'experiments/glass_heavy_scratches_001/render.py';spec=importlib.util.spec_from_file_location('glass_scratch_effect',source_path);glass=importlib.util.module_from_spec(spec);spec.loader.exec_module(glass)
    items=make_plan(config);t0=time.monotonic();write_json(OUT/'status.json',{'state':'preflighting','completed':0,'total':20})
    write_json(OUT/'config.json',{'count':20,'seed_base':config['seed'],'theta_definition':'signed camera pitch degrees','theta_absolute_max_exclusive':40,'yaw_range_deg':[-8,8],
        'lighting_styles':LIGHTS,'scratch_distribution':{'heavy':12,'medium':6,'light':2},'resolution_width':1200,'adaptive_height':True,
        'target_register_area_fraction':.9005,'blur_percent':0,'render_samples':32,'threads':8,'atlas':atlas,'rolling_geometry':rolling['geometry']})
    # Fit a range of image aspect ratios. Do not change the sampled theta or yaw.
    for item in items:
        passed=False;failures=[]
        for height in range(360,496,5):
            config['resolution']=[1200,height]
            try:
                _,_,_,_,framing=worker.setup(item,config,source,.75,ROOT/atlas['path'],rolling['geometry']);item['resolution']=[1200,height];item['preflight_framing']=framing;passed=True;break
            except ValueError as e:failures.append(str(e))
        if not passed:raise RuntimeError(f"No unclipped 90% framing for {item['sample_id']} theta={item['theta_deg']:.2f}, yaw={item['yaw_deg']:.2f}; {failures[-1]}")
        print('PREFLIGHT_OK',item['sample_id'],'theta',round(item['theta_deg'],2),'yaw',round(item['yaw_deg'],2),'resolution',item['resolution'],flush=True)
    write_json(OUT/'plan.json',{'count':20,'samples':items});write_json(OUT/'status.json',{'state':'rendering','completed':0,'total':20})
    for i,item in enumerate(items,1):
        config['resolution']=item['resolution'];scene,states,regions,resolved,framing=worker.setup(item,config,source,.75,ROOT/atlas['path'],rolling['geometry'])
        scene.cycles.samples=32;scene.cycles.device='CPU';scene.cycles.use_denoising=True;scene.cycles.seed=item['parameters']['seed'];scene.render.threads_mode='FIXED';scene.render.threads=8
        case=item['scratch'];glass.apply_glass_effect(case,{'seed':case['seed'],'scratch_mask_resolution':[1024,256]})
        stem=item['sample_id'];image=OUT/'images'/f'{stem}.png';label=OUT/'labels'/f'{stem}.txt';scene.render.filepath=str(image);bpy.ops.render.render(write_still=True)
        export_labels(label,[r['obb_px'] for r in regions],item['resolution'])
        write_json(OUT/'metadata'/f'{stem}.json',{**item,'wheel_states':states,'resolved_scene':resolved,'framing':framing,'regions':regions,
            'camera_matrix_world':list(map(list,scene.camera.matrix_world)),'camera_lens_mm':scene.camera.data.lens,'atlas':atlas,
            'image_sha256':worker.sha(image),'label_sha256':worker.sha(label),'source_scene_sha256':worker.sha(worker.SOURCE),
            'render':{'engine':'Cycles','device':'CPU','samples':32,'seed':scene.cycles.seed,'blender_version':bpy.app.version_string},
            'note':'Scratch texture affects only the glass surface. The OBB projects band geometry and does not correct refraction.'})
        write_json(OUT/'status.json',{'state':'rendering','completed':i,'total':20,'last_completed':stem,'elapsed_seconds':round(time.monotonic()-t0,2)})
        print('SCRATCH_MULTI_OK',stem,item['digits'],item['light_style'],case['name'],flush=True)
    write_json(OUT/'status.json',{'state':'complete','completed':20,'total':20,'elapsed_seconds':round(time.monotonic()-t0,2)})
    print('SCRATCH_MULTI_COMPLETE 20',flush=True)

if __name__=='__main__':
    try:main()
    except BaseException as e:
        if OUT.exists():
            p=OUT/'status.json';data=json.loads(p.read_text()) if p.exists() else {};data.update(state='failed',error=repr(e),traceback=traceback.format_exc());write_json(p,data)
        traceback.print_exc();raise
