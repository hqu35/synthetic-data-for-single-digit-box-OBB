"""Render heavily degraded 3D register photographs using existing scene and atlas."""
import argparse,copy,importlib.util,json,random,sys,time
from pathlib import Path
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import generate_vlm_exp as worker
import generate_scratch_multi as existing
from digitgen.assets import texture_spec,verify_spec
from digitgen.camera_appearance import process_image,read_png,write_png
from digitgen.export import export_labels,write_json
from digitgen.shear import make_shear_plan,apply_to_file,SHEAR_BUCKETS


def degrade_resolution(path, sensor_width):
    """Simulate low sensor resolution using bilinear down/up sampling, no crop."""
    rgb=read_png(path);h,w=rgb.shape[:2]
    target_h=max(1,round(h*sensor_width/w))
    def resize(arr, width, height):
        sh,sw=arr.shape[:2];x=np.clip((np.arange(width)+.5)*sw/width-.5,0,sw-1);y=np.clip((np.arange(height)+.5)*sh/height-.5,0,sh-1)
        xl=np.floor(x).astype(int);xr=np.minimum(xl+1,sw-1);xw=(x-xl)[None,:,None]
        yl=np.floor(y).astype(int);yr=np.minimum(yl+1,sh-1);yw=(y-yl)[:,None,None]
        return (arr[yl][:,xl]*(1-xw)+arr[yl][:,xr]*xw)*(1-yw)+(arr[yr][:,xl]*(1-xw)+arr[yr][:,xr]*xw)*yw
    low=resize(rgb.astype(np.float32),sensor_width,target_h)
    write_png(path,np.clip(np.rint(resize(low,w,h)),0,255).astype(np.uint8))
    return [sensor_width,target_h]


def add_stains(seed,strength):
    """Add seeded spatial surface contamination to the existing glass shader."""
    mat=bpy.data.objects['Continuous_glass_cover'].data.materials[0]
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
    existing_surface=output.inputs['Surface'].links[0].from_socket
    coord=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeMapping')
    rng=random.Random(seed);mapping.inputs['Location'].default_value=[rng.uniform(-15,15) for _ in range(3)]
    links.new(coord.outputs['Generated'],mapping.inputs['Vector'])
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=18;noise.inputs['Detail'].default_value=4;noise.inputs['Roughness'].default_value=.75
    links.new(mapping.outputs['Vector'],noise.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB');ramp.name='Surface stain coverage';ramp.color_ramp.elements[0].position=.42;ramp.color_ramp.elements[1].position=.68
    links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
    mult=nodes.new('ShaderNodeMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=strength;links.new(ramp.outputs['Color'],mult.inputs[0])
    dust=nodes.new('ShaderNodeBsdfDiffuse');dust.name='Dirty glass deposits';dust.inputs['Color'].default_value=(.25,.26,.24,1);dust.inputs['Roughness'].default_value=.8
    scratch=nodes.get('Seeded hairline surface mask')
    scratch_dust=nodes.new('ShaderNodeMath');scratch_dust.operation='MULTIPLY';scratch_dust.inputs[1].default_value=.4
    links.new(scratch.outputs['Color'],scratch_dust.inputs[0])
    coverage=nodes.new('ShaderNodeMath');coverage.operation='MAXIMUM';links.new(mult.outputs[0],coverage.inputs[0]);links.new(scratch_dust.outputs[0],coverage.inputs[1])
    mix=nodes.new('ShaderNodeMixShader');mix.name='Glass surface contamination';links.new(coverage.outputs[0],mix.inputs[0]);links.new(existing_surface,mix.inputs[1]);links.new(dust.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])


def broaden_surface_scratches(radius):
    """Broaden the existing surface mask before shading and sensor degradation."""
    if not radius:return
    node=bpy.data.objects['Continuous_glass_cover'].data.materials[0].node_tree.nodes['Seeded hairline surface mask']
    image=node.image;width,height=image.size
    pixels=np.empty(width*height*4,dtype=np.float32);image.pixels.foreach_get(pixels);pixels=pixels.reshape(height,width,4)
    mask=pixels[:,:,0];pad=np.pad(mask,radius,mode='edge');expanded=mask.copy()
    for dy in range(-radius,radius+1):
        for dx in range(-radius,radius+1):
            if dx*dx+dy*dy<=radius*radius:expanded=np.maximum(expanded,pad[radius+dy:radius+dy+height,radius+dx:radius+dx+width])
    pixels[:,:,:3]=expanded[:,:,None];image.pixels.foreach_set(pixels.ravel());image.update();image.pack()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='outputs/degraded_register_review');parser.add_argument('--count',type=int,default=5);parser.add_argument('--seed',type=int,default=2026110711);parser.add_argument('--sensor-width',type=int,default=240);parser.add_argument('--blur-percent',type=float,default=50);parser.add_argument('--stain-strength',type=float,default=.32);parser.add_argument('--scratch-count',type=int,default=170);parser.add_argument('--scratch-width',type=int,default=2,help='Surface scratch mask expansion in pixels (0 to 5)');parser.add_argument('--no-shear',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if not 1<=args.count<=20 or not 60<=args.sensor_width<=1200 or not 0<=args.blur_percent<=50 or not 0<=args.stain_strength<=1 or not 0<=args.scratch_count<=500 or not 0<=args.scratch_width<=5:parser.error('Parameter outside supported range')
    out=(ROOT/args.output).resolve();out.mkdir(parents=True,exist_ok=False)
    for name in ('images','labels','metadata'):(out/name).mkdir()
    c=existing.scene_config();c['seed']=args.seed;source=json.loads(worker.SOURCE_PARAMS.read_text());rolling=json.loads(worker.ROLLING_ATLAS_CONFIG.read_text());atlas=texture_spec(rolling);verify_spec(atlas)
    items=existing.make_plan(c)[:args.count]
    for item,shear in zip(items,make_shear_plan([x['parameters']['seed'] for x in items],not args.no_shear)):item['x_shear']=shear
    spec=importlib.util.spec_from_file_location('existing_glass_scratch',ROOT/'experiments/glass_heavy_scratches_001/render.py');glass=importlib.util.module_from_spec(spec);spec.loader.exec_module(glass)
    write_json(out/'config.json',{'arguments':vars(args),'atlas':atlas,'x_shear_buckets':[{'name':n,'weight':w,'range':[-b,b]} for n,w,b in SHEAR_BUCKETS],'degradation':'Bilinear downsample/upscale followed by linear-light Gaussian blur, sensor noise and X shear','note':'Projected OBBs do not include glass refraction.'})
    start=time.monotonic();write_json(out/'status.json',{'state':'rendering','completed':0,'total':args.count})
    for index,item in enumerate(items,1):
        for height in range(360,496,5):
            c['resolution']=[1200,height]
            try:scene,states,regions,resolved,framing=worker.setup(item,c,source,.75,ROOT/atlas['path'],rolling['geometry']);break
            except ValueError:continue
        else:raise RuntimeError('Could not fit register in camera')
        scene.cycles.samples=32;scene.cycles.device='CPU';scene.cycles.use_denoising=True;scene.cycles.seed=item['parameters']['seed'];scene.render.threads_mode='FIXED';scene.render.threads=8
        case={'name':'degraded','scratch_count':args.scratch_count,'scratch_strength':.72,'noise_strength':.6,'seed':item['parameters']['seed']+343}
        glass.apply_glass_effect(case,{'seed':case['seed'],'scratch_mask_resolution':[1024,256]});broaden_surface_scratches(args.scratch_width);add_stains(case['seed']+79,args.stain_strength)
        stem=item['sample_id'];image=out/'images'/f'{stem}.png';label=out/'labels'/f'{stem}.txt';scene.render.filepath=str(image);bpy.ops.render.render(write_still=True)
        sensor_res=degrade_resolution(image,args.sensor_width)
        processing={'camera_white_balance':[1,1,1],'postprocess_color_cast':[1,1,1],'camera_exposure':0,'contrast':.82,'blur_percent':args.blur_percent,'sensor_noise_std':.012,'noise_seed':case['seed']+3}
        process_image(image,image,processing);before=copy.deepcopy(framing);regions,framing,affine=apply_to_file(image,regions,framing,item['x_shear']['s']);export_labels(label,[r['obb_px'] for r in regions],affine['output_resolution'])
        write_json(out/'metadata'/f'{stem}.json',{**item,'atlas':atlas,'wheel_states':states,'resolved_scene':resolved,'camera_matrix_world':list(map(list,scene.camera.matrix_world)),'pre_shear_resolution':c['resolution'],'resolution':affine['output_resolution'],'image_affine':affine,'framing_before_shear':before,'framing':framing,'regions':regions,'sensor_resolution':sensor_res,'camera_processing':processing,'scratch':case,'stain_strength':args.stain_strength,'image_sha256':worker.sha(image),'label_sha256':worker.sha(label),'render':{'engine':'Cycles','samples':32,'blender_version':bpy.app.version_string}})
        write_json(out/'status.json',{'state':'rendering','completed':index,'total':args.count,'elapsed_seconds':round(time.monotonic()-start,1)})
        print('DEGRADED_OK',stem,item['digits'],flush=True)
    write_json(out/'status.json',{'state':'complete','completed':args.count,'total':args.count,'elapsed_seconds':round(time.monotonic()-start,1)});print('DEGRADED_COMPLETE',flush=True)
if __name__=='__main__':main()
