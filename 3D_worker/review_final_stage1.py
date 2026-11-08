"""Audit saved final Stage 1 inspection images and assemble comparison sheets."""
import argparse
import csv
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from digitgen.export import read_labels,write_json
from digitgen.geometry import area

ROOT=Path(__file__).resolve().parent


def comparison(out,names,labels,target,tile=500):
    font=ImageFont.truetype(str(ROOT/'assets/fonts/BarlowCondensed-Regular.ttf'),24)
    sheet=Image.new('RGB',(tile*len(names),tile+42),(22,25,30))
    for i,(name,label) in enumerate(zip(names,labels)):
        with Image.open(out/f'{name}.png') as loaded:
            im=loaded.convert('RGB');im.thumbnail((tile,tile));sheet.paste(im,(i*tile+(tile-im.width)//2,(tile-im.height)//2))
        ImageDraw.Draw(sheet).text((i*tile+12,tile+8),label,font=font,fill='white')
    sheet.save(out/target)


def review(out):
    out=Path(out);r=json.loads((out/'inspection_report.json').read_text())
    if r['training_dataset_generated'] or r['randomization']:raise ValueError('Expected fixed Stage 1 review only')
    d=r['layout']
    if abs(d['band_to_slot_ratio']-.70)>1e-10 or abs(d['band_center'])>1e-10:raise ValueError('Band is not centered at 70%')
    if abs(d['slot_width']-.640625)>1e-10 or abs(d['pitch']-.7175)>1e-10:raise ValueError('Physical slot changed')
    comparisons=[('A_three_visible_pins','B_four_visible_pins'),('D_previous_heavy_glyph','D_revised_regular_glyph'),('F_uniform_matte','F_slightly_glossy_ink')]
    for first,second in comparisons:
        a,b=r['views'][first],r['views'][second]
        for key in ('camera_matrix_world','camera_lens_mm','resolution','lights'):
            if a[key]!=b[key]:raise ValueError(f'Matched comparison changed {key}')
    for name,target in [('A_three_visible_pins',3),('B_four_visible_pins',4),('C_fixed_00054_register',3)]:
        for wheel in r['pin_visibility'][name]:
            if wheel['actually_visible_count']!=target or not wheel['all_visible_pins_fully_within_aperture']:
                raise ValueError('Visible pin target not satisfied')
            if min(wheel['adjacent_silhouette_clearance_px'])<3 or wheel['spacing_ratio']>1.12:raise ValueError('Merged/nonuniform pins')
    for name,v in r['views'].items():
        with Image.open(out/v['file']) as im:
            im.load()
            if im.format!='PNG' or list(im.size)!=v['resolution']:raise ValueError('Final PNG size or format mismatch')
    resolution=r['views']['C_fixed_00054_register']['resolution'];boxes=read_labels(out/'test_slot_obbs.txt',resolution)
    if len(boxes)!=5:raise ValueError('Expected five diagnostic physical-slot OBBs')
    for box,stored in zip(boxes,r['test_obb_corners_px']):
        if area(box)<=0 or any(not(0<=x<=resolution[0] and 0<=y<=resolution[1]) for x,y in box):raise ValueError('Invalid slot OBB')
        if max(abs(a-b) for pt,ref in zip(box,stored) for a,b in zip(pt,ref))>1e-5:raise ValueError('On-disk labels differ from rendered geometry')
    with Image.open(out/'C_fixed_00054_register.png') as source:
        image=source.convert('RGB');draw=ImageDraw.Draw(image)
        for i,box in enumerate(boxes):
            pts=[tuple(pt) for pt in box];draw.line(pts+[pts[0]],fill=(30,245,100),width=3)
            draw.text((pts[0][0]+5,pts[0][1]+5),f'slot {i}',fill=(30,245,100))
        image.save(out/'G_slot_obb_overlay.png')
    comparison(out,['A_three_visible_pins','B_four_visible_pins'],['3 visible pins','4 visible pins'],'pin_comparison.png')
    comparison(out,['D_previous_heavy_glyph','D_revised_regular_glyph'],['Previous SemiBold / original size','Regular / independent 0.82 scales'],'typography_comparison.png')
    comparison(out,['E_stable_4','E_4_to_5_025','E_4_to_5_050','E_4_to_5_075'],['4 stable','4 to 5: 0.25','4 to 5: 0.50','4 to 5: 0.75'],'rolling_sequence.png',360)
    comparison(out,['F_uniform_matte','F_slightly_glossy_ink'],['Uniform matte response','Smoother printed ink, same light'],'ink_surface_comparison.png',600)
    a=np.asarray(Image.open(out/'F_uniform_matte.png').convert('RGB')).astype(float)
    b=np.asarray(Image.open(out/'F_slightly_glossy_ink.png').convert('RGB')).astype(float)
    h,w=a.shape[:2];ys,xs=np.indices((h,w))
    ink=(a.mean(axis=2)<115)&(xs>.32*w)&(xs<.68*w)&(ys>.18*h)&(ys<.82*h)
    delta=b-a;values=delta[ink]
    surface={'ink_pixels_compared':int(ink.sum()),'mean_rgb_difference_8bit':float(values.mean()),
             'p99_absolute_channel_difference_8bit':float(np.percentile(np.abs(values),99)),
             'maximum_absolute_channel_difference_8bit':float(np.abs(values).max()),
             'meaning':'Measured render difference within the dark numeral region; visual inspection determines whether highlights are appropriately subtle.'}
    if surface['p99_absolute_channel_difference_8bit']<=1:raise ValueError('No measurable ink-surface response beyond renderer rounding')
    with (out/'pin_visibility.csv').open('w',newline='') as handle:
        writer=csv.writer(handle);writer.writerow(['view','wheel','total_pins','front_geometric_count','actually_visible','centers_px','spacing_px','silhouette_gaps_px','fully_inside'])
        for name,records in r['pin_visibility'].items():
            for wheel in records:writer.writerow([name,wheel['wheel'],wheel['total_pins'],wheel['geometric_front_center_count'],wheel['actually_visible_count'],json.dumps(wheel['projected_positions_px']),json.dumps(wheel['adjacent_projected_spacing_px']),json.dumps(wheel['adjacent_silhouette_clearance_px']),wheel['all_visible_pins_fully_within_aperture']])
    all_pairs={}
    for name,records in r['pin_visibility'].items():
        all_pairs[name]=[{'wheel':wheel['wheel'],'projected_positions_px':wheel['projected_positions_px'],
            'all_pairwise_spacing_px':[{'indices':[i,j],'distance':math.dist(a,b)}
                for i,a in enumerate(wheel['projected_positions_px']) for j,b in enumerate(wheel['projected_positions_px']) if i<j]}
            for wheel in records]
    write_json(out/'pin_pairwise_spacing.json',all_pairs)
    # Compact all-view sheet.
    tiles=[]
    for name,v in r['views'].items():
        with Image.open(out/v['file']) as source:im=source.convert('RGB');im.thumbnail((380,330))
        tile=Image.new('RGB',(400,365),(22,25,30));tile.paste(im,((400-im.width)//2,(330-im.height)//2))
        ImageDraw.Draw(tile).text((8,343),name,fill='white');tiles.append(tile)
    sheet=Image.new('RGB',(1200,math.ceil(len(tiles)/3)*365),(22,25,30))
    for i,tile in enumerate(tiles):sheet.paste(tile,((i%3)*400,(i//3)*365))
    sheet.save(out/'inspection_contact_sheet.png')
    saved=json.loads((out/'saved_scene_verification.json').read_text())
    if saved['status']!='passed':raise ValueError('Saved Blender scene checks did not pass')
    result={'status':'passed','stage':'Final Stage 1 review; human approval pending','images_decoded':len(r['views']),
            'reference_pin_counts':[w['actually_visible_count'] for w in r['pin_visibility']['C_fixed_00054_register']],
            'four_pin_variant':r['pin_visibility']['B_four_visible_pins'][0]['actually_visible_count'],
            'band_ratio':d['band_to_slot_ratio'],'band_center':d['band_center'],'test_obbs':5,
            'ink_surface_response':surface,'saved_scene_and_rolling_obb_verification':'passed',
            'training_dataset_generated':False,'randomization':False,'glass_added':False}
    write_json(out/'artifact_audit.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    review(parser.parse_args().output)
