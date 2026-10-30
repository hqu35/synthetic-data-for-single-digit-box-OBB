"""Inspect the saved single preview and create a separate label overlay."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
from digitgen.export import read_labels
from digitgen.geometry import area

ROOT=Path(__file__).resolve().parent
out=ROOT/'outputs/tight_framing_preview'
report=json.loads((out/'inspection_report.json').read_text());resolution=report['config']['resolution']
im=Image.open(out/'register_closeup.png');assert im.size==tuple(resolution) and im.format=='PNG'
im.load();polygon=report['register_footprint_polygon_px']
assert .90<=report['register_footprint_area_fraction']<=.95
assert abs(area(polygon)/(resolution[0]*resolution[1])-report['register_footprint_area_fraction'])<1e-8
mask=Image.new('1',tuple(resolution));ImageDraw.Draw(mask).polygon([tuple(p) for p in polygon],fill=1)
hist=mask.histogram();raster_fraction=(sum(hist)-hist[0])/(resolution[0]*resolution[1])
assert abs(raster_fraction-report['register_footprint_area_fraction'])<.005
boxes=read_labels(out/'register_closeup.txt',resolution);assert len(boxes)==5
overlay=im.convert('RGB');draw=ImageDraw.Draw(overlay);max_error=0
for i,(box,r) in enumerate(zip(boxes,report['regions'])):
    assert area(box)>0 and abs(r['band_to_slot_width_ratio']-.7)<1e-6
    assert all(0<=value<=resolution[j] for p in box for j,value in enumerate(p))
    max_error=max(max_error,max(abs(a-b) for p,q in zip(box,r['obb_px']) for a,b in zip(p,q)))
    xy=[tuple(p) for p in box];draw.line(xy+[xy[0]],fill='#35ff78',width=2)
    draw.text((box[0][0]+4,box[0][1]+4),str(i),fill='#35ff78')
assert max_error<1e-6
overlay.save(out/'register_closeup_overlay.png')
assert report['render_count']==1 and not report['dataset_resumed']
validation={'status':'passed','rgb_render_count':1,'resolution':resolution,
    'projected_register_area_fraction':report['register_footprint_area_fraction'],
    'rasterized_register_area_fraction':raster_fraction,
    'projected_background_area_fraction':report['background_area_fraction'],
    'complete_register_inside_frame':True,'digit_obb_count':5,'max_label_roundtrip_error_px':max_error,
    'dataset_resumed':False,'note':'Coverage measures the projected outer register silhouette, including its glass viewing window. The clean RGB has no label overlay.'}
(out/'validation_report.json').write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps(validation,indent=2))
