"""Audit fixed raised-band inspection outputs and draw diagnostic saved-label OBBs."""
import argparse
import json
import math
from pathlib import Path
from PIL import Image,ImageDraw
from digitgen.export import read_labels,write_json
from digitgen.geometry import area


def review(out):
    out=Path(out);report=json.loads((out/'inspection_report.json').read_text())
    if report['training_dataset_generated'] or report['randomization']:raise ValueError('Expected fixed geometry review only')
    if report['checks']['status']!='passed' or report['checks']['near_frontal_pin_visibility']['status']!='passed':
        raise ValueError('Raised geometry or near-frontal pin visibility check failed')
    for folder in ('images','labels','metadata'):
        if (out/folder).exists():raise ValueError('Unexpected dataset directories in Stage 1 output')
    before=report['views']['F_before_single_front'];after=report['views']['B_single_digit_front']
    for key in ('camera_matrix_world','camera_lens_mm','resolution','lights','material'):
        if before[key]!=after[key]:raise ValueError(f'Before/after changed viewing controls: {key}')
    row=report['views']['D_five_wheel_front'];resolution=row['resolution']
    boxes=read_labels(out/'test_slot_obbs.txt',resolution)
    if len(boxes)!=5:raise ValueError('Expected exactly one test slot OBB per wheel')
    for box,boundary,stored in zip(boxes,report['projected_slot_boundaries_px'],report['test_obb_corners_px']):
        if area(box)<=0 or any(not math.isfinite(v) for pt in box for v in pt):raise ValueError('Invalid corners')
        if any(not (0<=x<=resolution[0] and 0<=y<=resolution[1]) for x,y in box):raise ValueError('Out-of-image OBB')
        if max(abs(a-b) for pt,ref in zip(box,stored) for a,b in zip(pt,ref))>1e-5:raise ValueError('Saved-label mismatch')
        for point in boundary:
            for a,b in zip(box,box[1:]+box[:1]):
                if (b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])<-.001:
                    raise ValueError('OBB does not enclose visible aperture boundary')
    if any(sum(pt[0] for pt in b)<=sum(pt[0] for pt in a) for a,b in zip(boxes,boxes[1:])):
        raise ValueError('Incorrect physical slot ordering')
    with Image.open(out/row['file']) as source:
        image=source.convert('RGB');draw=ImageDraw.Draw(image)
        for i,box in enumerate(boxes):
            points=[tuple(pt) for pt in box];draw.line(points+[points[0]],fill=(30,245,100),width=3)
            draw.text((points[0][0]+5,points[0][1]+5),f'slot {i}',fill=(30,245,100))
        image.save(out/'D_front_test_obb_overlay.png')
    with Image.open(out/before['file']) as first,Image.open(out/after['file']) as second:
        pair=Image.new('RGB',(first.width+second.width,max(first.height,second.height)+35),(22,25,30))
        pair.paste(first,(0,0));pair.paste(second,(first.width,0));draw=ImageDraw.Draw(pair)
        draw.text((12,first.height+10),'BEFORE: full-width numeral drum, pins outside slot',fill='white')
        draw.text((first.width+12,second.height+10),'AFTER: narrow raised band, recessed sides, front-visible pins',fill='white')
        pair.save(out/'F_before_after_comparison.png')
    tiles=[]
    for name,view in report['views'].items():
        with Image.open(out/view['file']) as source:
            source.load()
            if source.format!='PNG' or list(source.size)!=view['resolution']:raise ValueError('Unexpected image size/format')
            thumb=source.convert('RGB');thumb.thumbnail((500,350))
        tile=Image.new('RGB',(500,380),(22,25,30));tile.paste(thumb,((500-thumb.width)//2,(350-thumb.height)//2))
        ImageDraw.Draw(tile).text((10,357),name,fill='white');tiles.append(tile)
    sheet=Image.new('RGB',(1000,math.ceil(len(tiles)/2)*380),(22,25,30))
    for i,tile in enumerate(tiles):sheet.paste(tile,((i%2)*500,(i//2)*380))
    sheet.save(out/'inspection_contact_sheet.png')
    result={'status':'passed','stage':'Stage 1 raised-band review; approval pending','images_decoded':len(tiles),
            'before_after_controls_identical':True,'test_slot_obbs':5,'near_frontal_pin_visibility':'passed',
            'geometry':'passed','randomization':False,'training_dataset_generated':False,
            'visual_acceptance':'Awaiting human approval; machine checks do not replace inspection.'}
    write_json(out/'artifact_audit.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    review(parser.parse_args().output)
