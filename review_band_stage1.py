"""Audit the single saved sample and create overlays from the exact exported labels."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np
from PIL import Image,ImageDraw
from digitgen.export import read_labels
from digitgen.geometry import area,minimum_rectangle

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='outputs/obb_band_stage1')
    args=parser.parse_args();out=ROOT/args.output
    report=json.loads((out/'inspection_report.json').read_text());res=report['resolution']
    assert report['rendered_rgb_count']==1 and not report['stage2_started']
    assert report['scene_signature_before']==report['scene_signature_after']
    assert report['implementation_sha256']==hashlib.sha256((ROOT/'digitgen/band_annotations.py').read_bytes()).hexdigest()
    im=Image.open(out/'000001.png').convert('RGB');assert im.size==tuple(res)
    boxes=read_labels(out/'000001.txt',res);assert len(boxes)==len(report['regions'])==5
    overlay=im.copy();draw=ImageDraw.Draw(overlay)
    diagnostic=im.copy();compare=ImageDraw.Draw(diagnostic)
    rows=[]
    for box,r in zip(boxes,report['regions']):
        assert np.isfinite(box).all() and (np.array(box)>=0).all() and (np.array(box)<=res).all()
        error=float(np.max(np.abs(np.array(box)-r['obb_px'])));assert error<1e-6
        assert area(box)>0
        e=np.diff(np.array(box+box[:1]),axis=0)
        assert abs(e[0]@e[1])<1e-5*np.linalg.norm(e[0])*np.linalg.norm(e[1])
        for p in r['visible_boundary_px']:
            for a,b in zip(box,box[1:]+box[:1]):
                assert (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])>=-1e-3
        assert abs(r['band_to_slot_width_ratio']-.7)<1e-6
        assert abs(r['left_margin_fraction']-.15)<1e-6 and abs(r['right_margin_fraction']-.15)<1e-6
        fitted,_=minimum_rectangle(r['visible_boundary_px']);assert abs(area(fitted)-area(box))<.001
        xy=[tuple(p) for p in box]
        draw.line(xy+[xy[0]],fill='#35ff78',width=2)
        draw.text((box[0][0]+4,box[0][1]+4),str(r['wheel']),fill='#35ff78')
        old=[tuple(p) for p in r['physical_slot_obb_px']]
        compare.line(old+[old[0]],fill='#ff8c5a',width=2)
        compare.line(xy+[xy[0]],fill='#35ff78',width=2)
        rows.append({'wheel':r['wheel'],'slot_width_units':r['physical_slot']['width'],
            'band_width_units':r['band_width'],'band_to_slot_width_ratio':r['band_to_slot_width_ratio'],
            'projected_obb_width_to_slot_ratio':r['projected_obb_width_to_slot_ratio'],
            'left_margin_fraction':r['left_margin_fraction'],'right_margin_fraction':r['right_margin_fraction'],
            'visible_region_to_obb_area_ratio':r['checks']['boundary_to_obb_area_ratio'],
            'max_saved_label_error_px':error})
    overlay.save(out/'000001_overlay.png')
    compare.rectangle((10,10,650,40),fill='#171717')
    compare.text((20,19),'Orange: old full-slot OBB   Green: corrected mesh-derived numeral-band OBB',fill='white')
    diagnostic.save(out/'old_vs_corrected.png')
    panel=Image.new('RGB',(res[0],res[1]*2+70),'#eeeeee');panel.paste(im,(0,35));panel.paste(overlay,(0,res[1]+70))
    label=ImageDraw.Draw(panel);label.text((15,10),'One deterministic RGB sample / preserved neutral-glass scene',fill='black')
    label.text((15,res[1]+45),'The same RGB / corrected YOLO-OBB labels read back from 000001.txt',fill='black')
    panel.save(out/'inspection_contact_sheet.png')
    source=ROOT/'outputs/glass_review/02_glass_neutral.png'
    source_diff=None
    if source.exists():
        original=np.asarray(Image.open(source).convert('RGB'),dtype=np.int16);current=np.asarray(im,dtype=np.int16)
        source_diff={'identical_rgb_pixels':bool(np.array_equal(original,current)),
                     'mean_absolute_channel_difference_8bit':float(np.abs(original-current).mean()),
                     'maximum_channel_difference_8bit':int(np.abs(original-current).max())}
    result={'status':'passed','sample_count':1,'labels_per_sample':5,'stage2_started':False,
            'geometry_material_atlas_camera_lighting_unchanged':True,
            'reference_rgb_comparison':source_diff,'measurements':rows,
            'visual_review':'Inspect green band edges against the cream raised band, not just black strokes. Orange boxes are diagnostic full-slot bounds only; excluded margins contain recessed mechanics and side pins.',
            'projection_limit':'Direct geometry projection; native glass introduces small optical shifts. No image-space shrink, clipping-to-frame repair or glyph-dependent fitting is performed.'}
    previous=ROOT/'outputs/glass_review/02_glass_neutral_slot_obbs.txt'
    if previous.exists():
        previous_boxes=read_labels(previous,res)
        result['historical_glass_overlay_height_check']={
            'historical_slot_obb_heights_px':[float(np.ptp(np.asarray(b)[:,1])) for b in previous_boxes],
            'actual_mesh_slot_obb_heights_px':[float(np.ptp(np.asarray(r['physical_slot_obb_px'])[:,1])) for r in report['regions']],
            'note':'Earlier glass diagnostics projected the front labels while the scene retained the 1600x700 oblique render aspect, then scaled to 1600x540. This review uses actual 1600x540 scene aspect and rejects mismatches. Historical delivery files are preserved.'}
    (out/'artifact_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    shutil.copy2('/tmp/band_projection_tests.log',out/'band_projection_tests.log')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
