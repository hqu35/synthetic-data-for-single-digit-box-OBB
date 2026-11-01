"""Validate real wheel UV tiles and projected vertical order in Blender."""
import json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import bpy
from generate_vlm_exp import setup,CONFIG,SOURCE_PARAMS,ROLLING_ATLAS_CONFIG
from digitgen.assets import texture_spec
old=json.loads((ROOT/'outputs/VLM_exp/metadata/000001.json').read_text());item={k:old[k] for k in ('sample_id','digits','transitions','parameters')}
c=json.loads(CONFIG.read_text());c['count']=100;c['camera'].pop('pose_overrides',None);c['resolution']=[1200,460]
r=json.loads(ROLLING_ATLAS_CONFIG.read_text());atlas=texture_spec(r);setup(item,c,json.loads(SOURCE_PARAMS.read_text()),.75,ROOT/atlas['path'],r['geometry'])
wheel=bpy.data.objects['wheel_2_raised_band'];axle=bpy.data.objects['wheel_2_axle'];root=bpy.data.objects['RegisterHousing'];mesh=wheel.data;segments=len(mesh.vertices)//4
for digit in range(10):
 axle.rotation_euler.x=-(digit+.5)*2*math.pi/10;bpy.context.view_layer.update();ys=[]
 for unwrapped in (digit,digit+1):
  expected=unwrapped%10;tile_index=r['typography']['tile_order'].index(expected)
  index=round(tile_index*segments/10)%segments;face=mesh.polygons[4*index]
  u=mesh.uv_layers.active.data[face.loop_indices[0]].uv.x;tile=math.floor((u%1)*10)
  if r['typography']['tile_order'][tile]!=expected:raise AssertionError(f'Wrong atlas tile: {digit=} {unwrapped=} {tile=}')
  v=mesh.vertices[index].co;y=(root.matrix_world.inverted()@wheel.matrix_world@v).y;ys.append(y)
 if not ys[0]>0>ys[1]:raise AssertionError(f'Wrong vertical order for {digit}: {ys}')
 print('DIRECTION_CHECK_OK',digit,'->',(digit+1)%10,'current_above_next_below',flush=True)
print('ALL_TEN_DIRECTION_CHECKS_PASS',flush=True)
