"""Generate the approved fixed-identity controlled experiment, then stop."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import bpy
import numpy as np
from digitgen.experiment1_sampling import sample_parameters
from digitgen.experiment1_scene import apply_parameters,immutable_signature,framing_check,optical_check,fit_register_camera,perspective_check
from digitgen.band_annotations import project_numeral_bands
from digitgen.export import export_labels,write_json
from digitgen.camera_appearance import process_image,read_png,blur_sigma_from_percent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def image_check(image,regions,config):
    rgb=read_png(image);lum=rgb@np.array([.2126,.7152,.0722]);checks=[]
    for r in regions:
        # An interior crop gives a conservative readability check; exact label
        # coverage is validated geometrically, independently of these pixels.
        box=np.asarray(r['obb_px']);center=box.mean(axis=0)
        x0,y0=np.ceil(center-(box.max(axis=0)-box.min(axis=0))*.22).astype(int)
        x1,y1=np.floor(center+(box.max(axis=0)-box.min(axis=0))*.22).astype(int)
        crop=lum[y0:y1,x0:x1];mean=float(crop.mean());std=float(crop.std());over=float((crop>248).mean())
        if mean<config['validation']['minimum_band_luminance_8bit'] or over>config['validation']['maximum_band_overexposed_fraction'] or std<8:
            raise ValueError(f'Band readability check failed for wheel {r["wheel"]}: mean={mean}, std={std}, over={over}')
        checks.append({'wheel':r['wheel'],'interior_luminance_mean':mean,'interior_luminance_std':std,'overexposed_fraction':over})
    return checks


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',default='configs/perspective_review.json')
    parser.add_argument('--resume',action='store_true');parser.add_argument('--plan-only',action='store_true')
    parser.add_argument('--allow-legacy-framing',action='store_true',help='Explicitly allow old nearly frontal configurations for historical replay')
    parser.add_argument('--only',type=int,help='Render one original index for replay, into a config-selected separate output')
    parser.add_argument('--blur-percent',type=float,default=0,help='Gaussian blur strength, 0 through 50')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    blur_sigma_from_percent(args.blur_percent,(1600,460))
    config=json.loads((ROOT/args.config).read_text());out=ROOT/config['output']
    if args.blur_percent:
        config['blur_percent']=args.blur_percent
    if config['count'] not in (5,100,200) or not config['stage1_approved']:raise ValueError('Choose an approved review or dataset configuration')
    if 'min_perspective_disparity' not in config['camera'] and not args.allow_legacy_framing:
        raise ValueError('Legacy near-frontal framing was rejected. Use a perspective configuration or explicitly allow historical replay.')
    if not args.resume and out.exists() and any(out.iterdir()):raise ValueError('Output exists; use --resume to verify and continue it')
    for name in ['images','labels','metadata','previews']:(out/name).mkdir(parents=True,exist_ok=True)
    if (out/'config.json').exists() and json.loads((out/'config.json').read_text())!=config:raise ValueError('Resume config differs')
    write_json(out/'config.json',config);write_json(out/'classes.json',{'0':'digit_band'})
    source=json.loads((ROOT/config['source_parameters']).read_text());source_sha=sha(ROOT/config['source_scene'])
    implementation_sha=hashlib.sha256(b''.join((ROOT/name).read_bytes() for name in [
        'generate_diffusion_exp1.py','digitgen/experiment1_sampling.py','digitgen/experiment1_scene.py',
        'digitgen/band_annotations.py','digitgen/camera_appearance.py','digitgen/geometry.py','digitgen/export.py','digitgen/scene.py'])).hexdigest()
    existing={}
    planned_attempts={}
    if not args.plan_only and (out/'metadata/plan_validation.json').exists():
        previous_plan=json.loads((out/'metadata/plan_validation.json').read_text())
        planned_attempts={item['sample_id']:item['attempt'] for item in previous_plan['samples']}
    journal=out/'metadata/samples.jsonl'
    if journal.exists():
        for line in journal.read_text().splitlines():
            record=json.loads(line)
            if record['sample_id'] in existing:raise ValueError('Duplicate sample journal record')
            existing[record['sample_id']]=record
    indices=[args.only] if args.only else range(1,config['count']+1);baseline=None;planned=[]
    for index in indices:
        stem=f'{index:06d}'
        if stem in existing:
            old=existing[stem]
            if old['source_scene_sha256']!=source_sha:raise ValueError('Resume source scene differs')
            if old['implementation_sha256']!=implementation_sha:raise ValueError('Resume renderer implementation differs')
            if sha(out/'images'/f'{stem}.png')!=old['image_sha256'] or sha(out/'labels'/f'{stem}.txt')!=old['label_sha256']:
                raise ValueError('Resume artifact checksum mismatch')
            continue
        succeeded=False
        for attempt in range(planned_attempts.get(stem,0),config['validation']['max_attempts_per_sample']):
            p=sample_parameters(config,index,attempt);start=time.monotonic()
            phase='geometry'
            try:
                bpy.ops.wm.open_mainfile(filepath=str(ROOT/config['source_scene']))
                before=immutable_signature()
                if baseline is None:baseline=before
                if before!=baseline:raise AssertionError('Approved source invariants changed')
                resolved=apply_parameters(config,p,source)
                framing=fit_register_camera(config,p)
                perspective=perspective_check(config,source)
                resolved.update({'camera_matrix_world':list(map(list,bpy.context.scene.camera.matrix_world)),
                    'camera_focal_length_mm':bpy.context.scene.camera.data.lens,
                    'camera_fov_degrees':__import__('math').degrees(bpy.context.scene.camera.data.angle),
                    'camera_sensor_shift_xy':[bpy.context.scene.camera.data.shift_x,bpy.context.scene.camera.data.shift_y]})
                if immutable_signature()!=before:raise AssertionError('Mechanics, wheel state, atlas or glass changed')
                frame=framing_check(config,source);scene=bpy.context.scene
                regions=project_numeral_bands(scene,scene.camera,bpy.data.objects['RegisterHousing'],config['resolution'])
                if any(r['checks']['boundary_to_obb_area_ratio']<config['validation']['minimum_boundary_to_obb_area_ratio'] for r in regions):
                    raise ValueError('Perspective rectangle has excessive blank area')
                optics=optical_check(config,regions,source)
                if args.plan_only:
                    planned.append({'sample_id':stem,'attempt':attempt,'seed':p['seed'],'optical_checks':optics,
                        'framing':framing,'perspective':perspective,
                        'min_region_to_obb_area_ratio':min(r['checks']['boundary_to_obb_area_ratio'] for r in regions)})
                    succeeded=True;break
                image=out/'images'/f'{stem}.png';labels=out/'labels'/f'{stem}.txt'
                phase='render';scene.render.filepath=str(image);bpy.ops.render.render(write_still=True)
                ap=p['appearance'];processing={'camera_white_balance':[1,1,1],'postprocess_color_cast':[1,1,1],
                    'camera_exposure':0,'contrast':ap['contrast'],'blur_percent':args.blur_percent,
                    'sensor_noise_std':ap['sensor_noise_std'],'noise_seed':ap['noise_seed']}
                phase='postprocess';process_image(image,image,processing);readability=image_check(image,regions,config)
                export_labels(labels,[r['obb_px'] for r in regions],config['resolution'])
                info={'sample_id':stem,'parameters':p,'seed':p['seed'],'attempt':attempt,
                    'true_digit_sequence':'00054','wheel_states':source['approved_wheel_states'],
                    'implementation_sha256':implementation_sha,
                    'source_scene_sha256':source_sha,'immutable_geometry_atlas_glass_signature':before,
                    'stable_atlas':source['source_stable_atlas'],'resolution':config['resolution'],
                    'resolved_scene':resolved,'render':{**config['render'],'seed':scene.cycles.seed,'blender_version':bpy.app.version_string,
                        'max_bounces':scene.cycles.max_bounces,'transmission_bounces':scene.cycles.transmission_bounces,
                        'glossy_bounces':scene.cycles.glossy_bounces,'pixel_aspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y]},
                    'camera_processing':processing,'projected_cover_corners_px':frame,'regions':regions,
                    'framing':framing,'perspective':perspective,
                    'optical_alignment':optics,'readability':readability,'image_sha256':sha(image),'label_sha256':sha(labels),
                    'elapsed_seconds':time.monotonic()-start,
                    'annotation_policy':'Class 0 = visible numeral-bearing band; original direct 3D projections retained. Ideal glass diagnostics do not refit labels.'}
                write_json(out/'metadata'/f'{stem}.json',info)
                with journal.open('a') as f:f.write(json.dumps(info,allow_nan=False)+'\n');f.flush()
                print('EXP1_SAMPLE_OK',stem,'attempt',attempt,'seconds',round(info['elapsed_seconds'],2),flush=True)
                succeeded=True;break
            except Exception as exc:
                failure={'sample_id':stem,'attempt':attempt,'seed':p['seed'],'parameters':p,'error':repr(exc),
                    'traceback':traceback.format_exc(),'elapsed_seconds':time.monotonic()-start,'mode':'plan' if args.plan_only else 'render',
                    'phase':phase,'image_file_created':(out/'images'/f'{stem}.png').exists()}
                with (out/'metadata/failures.jsonl').open('a') as f:f.write(json.dumps(failure)+'\n')
                print('EXP1_ATTEMPT_FAILED',stem,attempt,repr(exc),flush=True)
                # Preserve every failed rendered attempt outside the final pair directories.
                failed=out/'metadata/failed_attempts'/f'{stem}_attempt_{attempt}'
                for name,suffix in [('images','.png'),('labels','.txt')]:
                    artifact=out/name/f'{stem}{suffix}'
                    if artifact.exists():failed.mkdir(parents=True,exist_ok=True);artifact.replace(failed/artifact.name)
        if not succeeded:raise RuntimeError(f'Bounded attempts exhausted for sample {stem}; failures are logged')
    if args.plan_only:
        write_json(out/'metadata/plan_validation.json',{'status':'passed','rendered_images':0,'samples':planned})
    else:
        print('EXP1_RENDERING_COMPLETE_STOP',flush=True)


if __name__=='__main__':main()
