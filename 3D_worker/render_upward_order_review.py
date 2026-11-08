"""Render increasing digits moving upward through the 3D register."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import bpy
from generate_vlm_exp import setup,CONFIG,SOURCE_PARAMS,ROLLING_ATLAS_CONFIG,sha
from digitgen.assets import texture_spec,verify_spec
from digitgen.export import write_json,export_labels
from digitgen.camera_appearance import process_image
out=ROOT/'outputs/upward_order_review'
if out.exists() and any(out.iterdir()):raise ValueError('Output directory exists')
for sub in ('images','labels','metadata'): (out/sub).mkdir(parents=True,exist_ok=True)
old=json.loads((ROOT/'outputs/VLM_exp/metadata/000001.json').read_text());base={k:old[k] for k in ('sample_id','digits','transitions','parameters')}
c=json.loads(CONFIG.read_text());c['count']=100;c['camera'].pop('pose_overrides',None);c['resolution']=[1200,460]
source=json.loads(SOURCE_PARAMS.read_text());rolling=json.loads(ROLLING_ATLAS_CONFIG.read_text());atlas=texture_spec(rolling);verify_spec(atlas)
for name,digit,progress in [('3_to_4_000',3,0),('3_to_4_050',3,.5),('3_to_4_100',4,0),('4_to_5_050',4,.5),('9_to_0_050',9,.5)]:
 item=copy.deepcopy(base);item['digits']=f'00{digit}00';item['transitions']=[0,0,progress,0,0]
 scene,states,regions,resolved,framing=setup(item,c,source,.75,ROOT/atlas['path'],rolling['geometry'])
 image=out/'images'/f'{name}.png';label=out/'labels'/f'{name}.txt';scene.render.filepath=str(image);bpy.ops.render.render(write_still=True)
 processing=copy.deepcopy(old['camera_processing']);process_image(image,image,processing);export_labels(label,[r['obb_px'] for r in regions],c['resolution'])
 write_json(out/'metadata'/f'{name}.json',{'current_digit':digit,'next_digit':(digit+1)%10,'progress':progress,'wheel_states':states,'atlas':atlas,'regions':regions,'image_sha256':sha(image),'label_sha256':sha(label)})
 print('UPWARD_REVIEW_OK',name,flush=True)
print('UPWARD_REVIEW_COMPLETE',flush=True)
