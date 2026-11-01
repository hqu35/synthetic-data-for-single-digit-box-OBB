"""Render controlled physical-glass surface experiments in the 3D worker."""
import argparse,copy,hashlib,json,math,random,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT))
import bpy
import numpy as np
from generate_vlm_exp import setup,CONFIG,SOURCE_PARAMS,ROLLING_ATLAS_CONFIG,sha
from digitgen.assets import texture_spec,verify_spec
from digitgen.export import export_labels,write_json


def make_scratch_image(case, config):
    """Draw a seeded, softly antialiased surface height/roughness mask in Blender."""
    width,height=config['scratch_mask_resolution']; mask=np.zeros((height,width),dtype=np.float32)
    rng=random.Random(config['seed'])
    for k in range(case['scratch_count']):
        x=rng.uniform(width*.05,width*.95);y=rng.uniform(height*.08,height*.92)
        angle=rng.uniform(-math.pi,math.pi);length=rng.uniform(22,150)
        strength=rng.uniform(.25,.55) if k%7 else rng.uniform(.6,.9)
        thickness=rng.uniform(.45,.9);bend=rng.uniform(-.20,.20)
        steps=max(2,int(length*2))
        for j in range(steps+1):
            u=j/steps;theta=angle+bend*(u-.5);px=x+math.cos(theta)*length*(u-.5);py=y+math.sin(theta)*length*(u-.5)
            # Fade each tip and gently modulate the imperfect hairline.
            amp=strength*min(1,u*9,(1-u)*9)*(0.85+.15*math.sin(u*23+k))
            for ix in range(max(0,int(px)-2),min(width,int(px)+3)):
                for iy in range(max(0,int(py)-2),min(height,int(py)+3)):
                    value=amp*math.exp(-((ix-px)**2+(iy-py)**2)/(2*thickness**2))
                    if value>mask[iy,ix]:mask[iy,ix]=value
    rgba=np.ones((height,width,4),dtype=np.float32);rgba[:,:,:3]=mask[:,:,None]
    image=bpy.data.images.new('Seeded glass hairline mask',width=width,height=height,alpha=True,float_buffer=False)
    image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(rgba.ravel());image.update();image.pack()
    return image


def apply_glass_effect(case, config):
    glass=bpy.data.objects['Continuous_glass_cover'];original=glass.data.materials[0]
    if not case['scratch_strength'] and not case['noise_strength']:return
    material=original.copy();material.name='Experimental glass '+case['name'];glass.data.materials[0]=material
    nodes=material.node_tree.nodes;links=material.node_tree.links;bsdf=nodes.get('Principled BSDF');base=float(bsdf.inputs['Roughness'].default_value)
    coord=nodes.new('ShaderNodeTexCoord');coord.name='Glass local generated coordinates'
    contributions=[]
    if case['scratch_strength']:
        texture=nodes.new('ShaderNodeTexImage');texture.name='Seeded hairline surface mask';texture.image=make_scratch_image(case,config);texture.interpolation='Linear';texture.extension='CLIP'
        links.new(coord.outputs['Generated'],texture.inputs['Vector'])
        scratch=nodes.new('ShaderNodeMath');scratch.operation='MULTIPLY';scratch.inputs[1].default_value=case['scratch_strength'];links.new(texture.outputs['Color'],scratch.inputs[0]);contributions.append(scratch.outputs[0])
    if case['noise_strength']:
        noise=nodes.new('ShaderNodeTexNoise');noise.name='Glass microtexture';noise.inputs['Scale'].default_value=190;noise.inputs['Detail'].default_value=3
        links.new(coord.outputs['Generated'],noise.inputs['Vector'])
        noise_map=nodes.new('ShaderNodeMapRange');noise_map.inputs['From Min'].default_value=0;noise_map.inputs['From Max'].default_value=1
        noise_map.inputs['To Min'].default_value=0;noise_map.inputs['To Max'].default_value=.025*case['noise_strength'];links.new(noise.outputs['Fac'],noise_map.inputs['Value']);contributions.append(noise_map.outputs['Result'])
    add=nodes.new('ShaderNodeMath');add.operation='ADD';add.inputs[0].default_value=base;links.new(contributions[0],add.inputs[1]);rough=add.outputs[0]
    if len(contributions)>1:
        add2=nodes.new('ShaderNodeMath');add2.operation='ADD';links.new(rough,add2.inputs[0]);links.new(contributions[1],add2.inputs[1]);rough=add2.outputs[0]
    links.new(rough,bsdf.inputs['Roughness'])
    bump=nodes.new('ShaderNodeBump');bump.name='Fine glass normal variation';bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.0007
    links.new(contributions[0],bump.inputs['Height']);links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])


def geometry_signature():
    h=hashlib.sha256()
    for o in sorted((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:o.name):
        h.update(o.name.encode());h.update(str([list(row) for row in o.matrix_world]).encode())
        for v in o.data.vertices:h.update(str(tuple(v.co)).encode())
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default=str(HERE/'results_initial_replay'));args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    out=Path(args.output).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('Choose a new empty output directory')
    for d in ('images','labels','metadata'):(out/d).mkdir(parents=True,exist_ok=True)
    config=json.loads((HERE/'config_initial.json').read_text());old=json.loads((HERE/'fixed_sample.json').read_text());item={k:old[k] for k in ('sample_id','digits','transitions','parameters')}
    c=json.loads(CONFIG.read_text());c['count']=100;c['camera'].pop('pose_overrides',None);c['resolution']=config['resolution']
    source=json.loads(SOURCE_PARAMS.read_text());rolling=json.loads(ROLLING_ATLAS_CONFIG.read_text());atlas=texture_spec(rolling);verify_spec(atlas)
    reference=None
    for case in config['cases']:
        scene,states,regions,resolved,framing=setup(item,c,source,config['width_scale'],ROOT/atlas['path'],rolling['geometry'])
        scene.cycles.samples=config['samples'];scene.cycles.seed=config['seed'];scene.render.threads=config['threads']
        signature=geometry_signature();camera=[list(row) for row in scene.camera.matrix_world];boxes=[r['obb_px'] for r in regions]
        invariants={'geometry_sha256':signature,'camera_matrix_world':camera,'camera_lens_mm':scene.camera.data.lens,'digit_states':states,'boxes':boxes,'lighting':resolved['lights'],'resolution':config['resolution']}
        if reference is None:reference=copy.deepcopy(invariants)
        elif invariants!=reference:raise AssertionError('Scene invariants differ between cases')
        apply_glass_effect(case,config)
        image=out/'images'/f"{case['name']}.png";scene.render.filepath=str(image);bpy.ops.render.render(write_still=True)
        label=out/'labels'/f"{case['name']}.txt";export_labels(label,boxes,config['resolution'])
        write_json(out/'metadata'/f"{case['name']}.json",{'case':case,'seed':config['seed'],'invariants':invariants,'atlas':atlas,'image_sha256':sha(image),'label_sha256':sha(label),'scene_samples':config['samples'],'postprocessing':'none; native Blender RGB render'})
        print('GLASS_EXPERIMENT_OK',case['name'],flush=True)
    write_json(out/'validation.json',{'case_count':len(config['cases']),'geometry_camera_lights_states_boxes':'identical across all cases','samples':config['samples'],'atlas':atlas,'method':'same scene reloaded for each render; material modified on glass only; no postprocessing'})
    print('GLASS_EXPERIMENT_COMPLETE',flush=True)

if __name__=='__main__':main()
