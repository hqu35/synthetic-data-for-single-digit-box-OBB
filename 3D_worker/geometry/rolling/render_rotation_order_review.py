"""Render three 3D rolling transitions to inspect digit order and direction."""

# Load the single shared package without worker-local asset links.
import sys as _shared_sys
from pathlib import Path as _SharedPath
_shared_sys.path.insert(0, str(next(p / 'shared' for p in _SharedPath(__file__).resolve().parents if (p / 'shared' / 'digitgen').is_dir())))
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import bpy
from scene.scene_core import setup,CONFIG,SOURCE_PARAMS,ROLLING_ATLAS_CONFIG,sha
from digitgen.assets import texture_spec,verify_spec
from digitgen.export import write_json,export_labels
from digitgen.camera_appearance import process_image
out=ROOT/'outputs/rotation_order_review'
if out.exists() and any(out.iterdir()):raise ValueError('Output directory exists')
for sub in ('images','labels','metadata'): (out/sub).mkdir(parents=True,exist_ok=True)
old=json.loads((ROOT/'outputs/scratch_multi_version/metadata/000001.json').read_text());base={k:old[k] for k in ('sample_id','digits','transitions','parameters')}
c=json.loads(CONFIG.read_text());c['count']=100;c['camera'].pop('pose_overrides',None);c['resolution']=[1200,460]
source=json.loads(SOURCE_PARAMS.read_text());rolling=json.loads(ROLLING_ATLAS_CONFIG.read_text());atlas=texture_spec(rolling);verify_spec(atlas)
for digit in (3,4,9):
 nxt=(digit+1)%10;name=f'{digit}_to_{nxt}';item=copy.deepcopy(base);item['digits']=f'00{digit}00';item['transitions']=[0,0,.5,0,0]
 scene,states,regions,resolved,framing=setup(item,c,source,.75,ROOT.parent/'shared'/atlas['path'],rolling['geometry'])
 image=out/'images'/f'{name}.png';label=out/'labels'/f'{name}.txt';scene.render.filepath=str(image);bpy.ops.render.render(write_still=True)
 processing=copy.deepcopy(old['camera_processing']);process_image(image,image,processing);export_labels(label,[r['obb_px'] for r in regions],c['resolution'])
 write_json(out/'metadata'/f'{name}.json',{'current_digit':digit,'next_digit':nxt,'progress':.5,'wheel_states':states,'atlas':atlas,'regions':regions,'image_sha256':sha(image),'label_sha256':sha(label)})
 print('ROTATION_ORDER_OK',name,flush=True)
print('ROTATION_ORDER_COMPLETE',flush=True)
