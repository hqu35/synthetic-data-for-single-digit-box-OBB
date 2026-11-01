"""Save the heavy-scratch glass example as a self-contained Blender scene."""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE));sys.path.insert(0,str(ROOT))
import bpy
import render as experiment
from digitgen.assets import texture_spec,verify_spec
config=json.loads((HERE/'config.json').read_text());old=json.loads((HERE/'fixed_sample.json').read_text());item={k:old[k] for k in ('sample_id','digits','transitions','parameters')}
c=json.loads(experiment.CONFIG.read_text());c['count']=100;c['camera'].pop('pose_overrides',None);c['resolution']=config['resolution']
source=json.loads(experiment.SOURCE_PARAMS.read_text());rolling=json.loads(experiment.ROLLING_ATLAS_CONFIG.read_text());atlas=texture_spec(rolling);verify_spec(atlas)
scene,_,_,_,_=experiment.setup(item,c,source,config['width_scale'],ROOT/atlas['path'],rolling['geometry']);scene.cycles.samples=config['samples'];scene.cycles.seed=config['seed'];scene.render.threads=config['threads']
experiment.apply_glass_effect(config['cases'][1],config)
for image in bpy.data.images:
 if image.source=='FILE' and not image.packed_file:image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'results/heavy_scratch_scene.blend'))
print('HEAVY_SCENE_SAVED',flush=True)
