"""Validate every Experiment 1 pair and create English review previews."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from digitgen.export import read_labels
from digitgen.geometry import area,minimum_rectangle

ROOT=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sheet(out,records,name,columns,tile_width,overlay=False):
    height=round(tile_width*records[0]['resolution'][1]/records[0]['resolution'][0]);cell_height=height+30
    result=Image.new('RGB',(columns*tile_width,math.ceil(len(records)/columns)*cell_height),'#eeeeee')
    draw=ImageDraw.Draw(result)
    for j,r in enumerate(records):
        stem=r['sample_id'];file=out/'previews'/f'{stem}_overlay.png' if overlay else out/'images'/f'{stem}.png'
        im=Image.open(file).convert('RGB');im=im.resize((tile_width,height))
        x=j%columns*tile_width;y=j//columns*cell_height;result.paste(im,(x,y+30))
        camera=r['parameters']['camera'];preset=r['parameters']['lighting']['preset']
        caption=f'{stem} | {preset} | yaw {camera["yaw_deg"]:+.1f} / pitch {camera["pitch_deg"]:+.1f} / roll {camera["roll_deg"]:+.1f}'
        draw.text((x+7,y+8),caption,fill='black')
    result.save(out/'previews'/name)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='diffusion_model_dataset/exp1')
    args=parser.parse_args();out=ROOT/args.output;config=json.loads((out/'config.json').read_text());res=config['resolution']
    records=[json.loads(line) for line in (out/'metadata/samples.jsonl').read_text().splitlines()]
    count=config['count'];expected={f'{i:06d}' for i in range(1,count+1)}
    assert len(records)==count and {r['sample_id'] for r in records}==expected
    assert {p.stem for p in (out/'images').glob('*.png')}==expected
    assert {p.stem for p in (out/'labels').glob('*.txt')}==expected
    assert {p.stem for p in (out/'metadata').glob('[0-9]*.json')}==expected
    assert len({r['immutable_geometry_atlas_glass_signature'] for r in records})==1
    assert len({r['implementation_sha256'] for r in records})==1
    assert len({r['seed'] for r in records})==count
    assert len({r['image_sha256'] for r in records})==count
    assert len({json.dumps(r['resolved_scene']['camera_matrix_world']) for r in records})==count
    assert len({json.dumps(r['resolved_scene']['lights'],sort_keys=True) for r in records})==count
    widths=[];tightness=[];shifts=[];fractions=[];luminances=[];coverage=[];fitted_lenses=[];projected_roll=[];disparities=[];count_noise=0;roundtrip=0;manifest=[]
    for r in records:
        stem=r['sample_id'];image=out/'images'/f'{stem}.png';label=out/'labels'/f'{stem}.txt'
        assert json.loads((out/'metadata'/f'{stem}.json').read_text())==r
        assert sha(image)==r['image_sha256'] and sha(label)==r['label_sha256']
        manifest.extend([{'path':f'images/{stem}.png','sha256':r['image_sha256']},{'path':f'labels/{stem}.txt','sha256':r['label_sha256']}])
        with Image.open(image) as im:
            assert im.size==tuple(res) and im.format=='PNG';im.load()
            assert im.mode=='RGB'
            rgb=np.asarray(im)
        if config['camera'].get('auto_fit_register'):
            frame=r['framing'];fraction=area(frame['register_footprint_polygon_px'])/(res[0]*res[1])
            assert abs(fraction-frame['register_area_fraction'])<1e-8
            assert .90<=fraction<=.95
            assert all(0<p[0]<res[0] and 0<p[1]<res[1] for p in frame['register_footprint_polygon_px'])
            coverage.append(fraction);fitted_lenses.append(frame['fitted_focal_length_mm']);projected_roll.append(frame['projected_register_roll_deg'])
        if 'min_perspective_disparity' in config['camera']:
            perspective=r['perspective'];quad=perspective['glass_front_quad_px']
            left=math.dist(quad[0],quad[3]);right=math.dist(quad[1],quad[2])
            disparity=(right-left)/((right+left)/2)
            assert perspective['camera_projection']=='PERSP'
            assert abs(disparity-perspective['signed_opposite_edge_disparity'])<1e-9
            assert config['camera']['min_perspective_disparity']<=abs(disparity)<=config['camera']['max_perspective_disparity']
            disparities.append(disparity)
        assert r['true_digit_sequence']=='00054' and [w['transition_progress'] for w in r['wheel_states']]==[0,0,0,0,.05]
        assert [w['digit'] for w in r['wheel_states']]==[0,0,0,5,4]
        boxes=read_labels(label,res);assert len(boxes)==len(r['regions'])==5
        for box,region,optics in zip(boxes,r['regions'],r['optical_alignment']):
            assert np.isfinite(box).all() and (np.array(box)>=0).all() and (np.array(box)<=res).all()
            assert area(box)>25
            e=np.diff(np.array(box+box[:1]),axis=0)
            assert abs(e[0]@e[1])<1e-6*np.linalg.norm(e[0])*np.linalg.norm(e[1])
            error=float(np.max(np.abs(np.asarray(box)-region['obb_px'])));roundtrip=max(roundtrip,error);assert error<1e-6
            for point in region['visible_boundary_px']:
                for a,b in zip(box,box[1:]+box[:1]):
                    assert (b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])>=-1e-3
            exact,_=minimum_rectangle(region['visible_boundary_px']);assert abs(area(exact)-area(box))<.001
            assert abs(region['band_to_slot_width_ratio']-.70)<2e-6
            assert abs(region['left_margin_fraction']-.15)<2e-6 and abs(region['right_margin_fraction']-.15)<2e-6
            assert region['checks']['boundary_to_obb_area_ratio']>=config['validation']['minimum_boundary_to_obb_area_ratio']
            assert optics['optical_paths_inside_cover'] and optics['visibility_rays_passed']==3
            assert optics['max_shift_fraction_of_band_width']<=config['validation']['maximum_ideal_glass_shift_fraction_of_band_width']
            widths.append(region['projected_obb_width_to_slot_ratio']);tightness.append(region['checks']['boundary_to_obb_area_ratio'])
            shifts.append(optics['max_ideal_glass_shift_px']);fractions.append(optics['max_shift_fraction_of_band_width'])
            # Independent final-pixel luminance check inside the projected band.
            mask=Image.new('1',tuple(res));ImageDraw.Draw(mask).polygon([tuple(p) for p in region['visible_boundary_px']],fill=1)
            values=rgb[np.asarray(mask,dtype=bool)]@np.array([.2126,.7152,.0722])
            luminances.append(float(values.mean()))
            assert values.mean()>config['validation']['minimum_band_luminance_8bit'] and values.std()>8
            assert np.mean(values>248)<=config['validation']['maximum_band_overexposed_fraction']
        count_noise+=r['camera_processing']['sensor_noise_std']>0
    records.sort(key=lambda r:r['sample_id'])
    # Select camera and exposure extremes, plus both illumination presets.
    chosen={0,1,count//2-1,count-1}
    for group,key in [('camera','yaw_deg'),('camera','pitch_deg'),('camera','roll_deg'),('appearance','exposure_ev')]:
        chosen.add(min(range(count),key=lambda i:records[i]['parameters'][group][key]))
        chosen.add(max(range(count),key=lambda i:records[i]['parameters'][group][key]))
    for i in range(0,count,max(1,count//12)):
        if len(chosen)>=min(12,count):break
        chosen.add(i)
    selected=[records[i] for i in sorted(chosen)]
    for r in selected:
        stem=r['sample_id'];im=Image.open(out/'images'/f'{stem}.png').convert('RGB');draw=ImageDraw.Draw(im)
        for digit,box in enumerate(read_labels(out/'labels'/f'{stem}.txt',res)):
            xy=[tuple(p) for p in box];draw.line(xy+[xy[0]],fill='#35ff78',width=2)
            draw.text((box[0][0]+4,box[0][1]+4),str(digit),fill='#35ff78')
        im.save(out/'previews'/f'{stem}_overlay.png')
    sheet(out,selected,'contact_sheet.png',3,640)
    sheet(out,selected,'overlay_contact_sheet.png',3,640,True)
    sheet(out,records,f'all_{count}_contact_sheet.png',5,384)
    for start in range(0,count,40):
        sheet(out,records[start:start+40],f'overview_{start+1:03d}_{min(count,start+40):03d}.png',5,384)
    def bounds(values):return {'minimum':float(min(values)),'maximum':float(max(values))}
    failures=[json.loads(s) for s in (out/'metadata/failures.jsonl').read_text().splitlines()] if (out/'metadata/failures.jsonl').exists() else []
    report={'status':'passed','images':count,'labels':count,'metadata_records':count,'boxes_per_image':5,'total_boxes':count*5,
        'all_rgb_images_unique':True,'distinct_camera_poses':count,'distinct_lighting_settings':count,
        'resolution':res,'classes':{'0':'digit_band'},'all_images_decoded':True,'all_labels_valid_normalized_clockwise_rectangles':True,
        'model_geometry_atlas_wheel_states_and_glass_preserved':True,'max_label_roundtrip_error_px':roundtrip,
        'mesh_band_to_slot_ratio':.7,'mesh_side_margin_fraction_each':.15,
        'projected_obb_width_to_slot_ratio':bounds(widths),'visible_region_to_obb_area_ratio':bounds(tightness),
        'ideal_glass_shift_px':bounds(shifts),'ideal_glass_shift_fraction_of_band_width':bounds(fractions),
        'final_band_luminance_8bit':bounds(luminances),
        'lighting_counts':{p:sum(r['parameters']['lighting']['preset']==p for r in records) for p in ['neutral','cool_blue']},
        'sensor_noise_enabled_count':int(count_noise),'render_failure_attempts':sum(f['mode']=='render' and f.get('phase')!='geometry' for f in failures),
        'render_run_geometry_rejections':sum(f['mode']=='render' and f.get('phase')=='geometry' for f in failures),
        'preflight_failure_events':sum(f['mode']=='plan' for f in failures),
        'failed_render_artifacts_preserved':True,'preview_sample_ids':[r['sample_id'] for r in selected],
        'register_coverage_fraction':bounds(coverage) if coverage else None,'fitted_focal_length_mm':bounds(fitted_lenses) if fitted_lenses else None,'projected_register_roll_deg':bounds(projected_roll) if projected_roll else None,
        'signed_perspective_disparity':bounds(disparities) if disparities else None,
        'camera_ranges':{key:bounds([r['parameters']['camera'][key] for r in records]) for key in ['yaw_deg','pitch_deg','roll_deg','distance','focal_length_mm']},
        'annotation_limits':'Ideal parallel-glass diagnostics exclude bevel and micro-normal effects. Direct projected band labels are retained; no refraction fitting. Minimum-area rectangles include small perspective corner regions. Review overlay extremes before downstream use.',
        'next_step':('Human review of the five perspective views. No larger dataset, FLUX inference, ComfyUI or training has been launched.'
                     if count==5 else 'Human-reviewed image-to-image experiment. No FLUX inference, ComfyUI or training has been launched.')}
    (out/'validation_report.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'dataset_manifest.sha256.json').write_text(json.dumps({'files':manifest},indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
