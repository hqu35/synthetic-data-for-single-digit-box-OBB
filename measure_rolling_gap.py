"""Measure stroke-to-stroke blank rows in the fixed 4-to-5 review camera crop.

This is a deliberately scoped pixel inspection, not a general glyph detector.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',default='outputs/rolling_gap_review')
parser.add_argument('--prefix',default='transition_')
args=parser.parse_args();p=Path(args.output);samples=[]
for state in (25,50,75):
    stem=f'{args.prefix}{state:03}';image=np.asarray(Image.open(p/'images'/f'{stem}.png').convert('RGB'))
    # Isolate center glyph from the mechanical pins and dividers. Dark ink rows
    # are taken directly from the final rendered RGB, with known-lighting crop.
    x0,x1=535,655;y0,y1=100,374
    counts=(image[y0:y1,x0:x1].max(axis=2)<65).sum(axis=1)
    rows=np.flatnonzero(counts>=3)+y0;groups=[]
    for row in rows:
        if not groups or row>groups[-1][-1]+1:groups.append([int(row)])
        else:groups[-1].append(int(row))
    groups=[g for g in groups if len(g)>=10]
    candidates=[(b[0]-a[-1]-1,a[-1],b[0]) for a,b in zip(groups,groups[1:])]
    if not candidates:raise ValueError(f'No two distinct visible strokes: {stem}')
    gap,upper,lower=max(candidates)
    meta=json.loads((p/'metadata'/f'{stem}.json').read_text());q=meta['regions'][2]['physical_slot_obb_px']
    h=math.dist(q[1],q[2]);ratio=gap/h
    samples.append({'progress':state/100,'upper_stroke_bottom_y_px':upper,'lower_stroke_top_y_px':lower,'visible_blank_rows_px':gap,'projected_box_height_px':h,'gap_ratio':ratio,'passes_0_09_to_0_12':.09<=ratio<=.12})
    print(f'{state:>2}%: gap={gap}px, box={h:.2f}px, ratio={ratio:.5f}',flush=True)
result={'method':'Threshold final RGB ink in a fixed crop of the central 4-to-5 wheel; count fully blank pixel rows between visible upper and lower strokes; divide by projected physical window OBB height.','threshold_rgb_max':64,'minimum_dark_pixels_per_row':3,'crop_xyxy':[x0,y0,x1,y1],'scope':'One scene, camera, lighting and digit pair; not all perspectives or digit pairs. Reflections and threshold selection can affect this measurement.','samples':samples,'all_checkpoints_pass':all(s['passes_0_09_to_0_12'] for s in samples)}
(p/'gap_measurements.json').write_text(json.dumps(result,indent=2)+'\n')
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',24);board=Image.new('RGB',(1200,3*360),'white');d=ImageDraw.Draw(board)
for i,s in enumerate(samples):
 im=Image.open(p/'images'/f"{args.prefix}{round(s['progress']*100):03}.png").convert('RGB');crop=im.crop((470,75,690,405));board.paste(im.resize((780,299)),(0,i*360+50));board.paste(crop,(850,i*360+25));top=i*360+25+s['upper_stroke_bottom_y_px']-75;bottom=i*360+25+s['lower_stroke_top_y_px']-75
 d.line((1080,top,1080,bottom),fill='#00a343',width=4);d.line((1073,top,1087,top),fill='#00a343',width=3);d.line((1073,bottom,1087,bottom),fill='#00a343',width=3)
 d.text((8,i*360+12),f"{round(s['progress']*100)}% progress   gap / box height = {s['gap_ratio']:.3f}",font=font,fill='black')
board.save(p/'inspection_contact_sheet.png')
if not result['all_checkpoints_pass']:raise ValueError('One or more measured gaps are outside 0.09 to 0.12')
