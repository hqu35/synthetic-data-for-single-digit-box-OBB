import copy,json,sys
from pathlib import Path
sys.path.insert(0,'/Users/ququ/synth_data_digit_box/synthetic-data-for-single-digit-box-OBB')
import bpy
from mathutils import Vector
from generate_vlm_exp import setup,ROOT,CONFIG,SOURCE_PARAMS
from digitgen.export import export_labels,write_json
from digitgen.camera_appearance import process_image
out=ROOT/'outputs/narrow_wheel_review'
if out.exists() and any(out.iterdir()):raise ValueError('Review directory exists')
for d in ('images','labels','metadata'): (out/d).mkdir(parents=True,exist_ok=True)
old=json.loads((ROOT/'outputs/VLM_exp/metadata/000001.json').read_text());item={k:old[k] for k in ('sample_id','digits','transitions','parameters')}
source=json.loads(SOURCE_PARAMS.read_text());base=json.loads(CONFIG.read_text());base['count']=100;base['camera'].pop('pose_overrides',None)
measure={}
for scale in (1.0,0.75):
 config=copy.deepcopy(base);config['resolution'][0]=round(1600*scale)
 scene,states,regions,resolved,framing=setup(item,config,source,scale)
 def bounds(name):
  o=bpy.data.objects[name];xs=[(o.matrix_world@v.co).x for v in o.data.vertices];return min(xs),max(xs)
 a=bounds('wheel_0_raised_band');b=bounds('wheel_1_raised_band')
 measure[str(scale)]={'wheel_band_width':a[1]-a[0],'neighbor_band_gap':b[0]-a[1],'resolution':config['resolution'],'framing':framing}
 name='original' if scale==1 else 'narrow_75_percent'
 img=out/'images'/f'{name}.png';scene.render.filepath=str(img);bpy.ops.render.render(write_still=True)
 p=copy.deepcopy(old['camera_processing']);process_image(img,img,p)
 export_labels(out/'labels'/f'{name}.txt',[r['obb_px'] for r in regions],config['resolution'])
 write_json(out/'metadata'/f'{name}.json',{'wheel_width_scale':scale,'measurement':measure[str(scale)],'regions':regions,'digits':item['digits'],'transitions':item['transitions'],'camera_processing':p,'resolved_scene':resolved})
 print('NARROW_REVIEW_OK',name,flush=True)
a=measure['1.0'];b=measure['0.75']
for field in ('wheel_band_width','neighbor_band_gap'):
 ratio=b[field]/a[field]
 if abs(ratio-.75)>1e-5:raise AssertionError(f'{field} ratio {ratio}')
write_json(out/'geometry_validation.json',{'measurements':measure,'band_width_ratio':b['wheel_band_width']/a['wheel_band_width'],'band_gap_ratio':b['neighbor_band_gap']/a['neighbor_band_gap'],'status':'passed'})
print('NARROW_REVIEW_COMPLETE',flush=True)
