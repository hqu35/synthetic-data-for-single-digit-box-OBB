"""blender --background --factory-startup --python generate.py -- --config configs/preview.json"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from digitgen.config import load_config, validate_config
from digitgen.export import export_labels, svg_overlay, write_json
from digitgen.geometry import validate_boxes
from digitgen.sampling import sample_parameters, wheel_state


def code_hash():
    files = [ROOT/'generate.py', *sorted((ROOT/'digitgen').glob('*.py'))]
    return hashlib.sha256(b''.join(p.read_bytes() for p in files)).hexdigest()


def export_sample(out, name, c, p, boxes, boundaries, scene):
    import bpy
    if len(boxes)!=p['digit_count'] or len(p['wheels'])!=p['digit_count']:
        raise ValueError('Incorrect physical slot/label count')
    p['measured_obb_angles_deg'] = validate_boxes(boxes,boundaries,c['resolution'],p['requested_angle_deg'],c['rotation'])
    for state, theta in zip(p['wheels'], p['measured_obb_angles_deg']):
        state['image_obb_theta_deg'] = theta
    if not p['wheel_width'] < p['pitch']:
        raise ValueError('Physical wheel overlap')
    image = out/'images'/f'{name}.png'
    raw_image=out/'raw_images'/f'{name}.png'
    scene.render.filepath = str(raw_image)
    bpy.ops.render.render(write_still=True)
    from digitgen.camera_appearance import process_image
    process_image(raw_image,image,p['photograph'])
    if not image.is_file():
        raise RuntimeError('Renderer did not export PNG')
    label = out/'labels'/f'{name}.txt'
    export_labels(label,boxes,c['resolution'])
    svg_overlay(image,label,out/'overlays'/f'{name}.svg',c['resolution'])
    meta = {'sample_id':name, 'schema_version':2, 'blender_version':bpy.app.version_string,
            'source_sha256':code_hash(), 'config':c, 'parameters':p,
            'resolution':c['resolution'], 'annotation_target':'visible opening through solid stationary frame; one per wheel; front/back projected intersection',
            'corner_order':'clockwise local TL, TR, BR, BL; width axis closest to image horizontal',
            'angle_convention':'degrees clockwise from image +x toward image +y (down)',
            'wheel_rotation_units':'radians about local +X; independent of image_obb_theta_deg',
            'obb_corners_px':boxes, 'projected_boundaries_px':boundaries,
            'validation':{'geometry':'passed', 'projection':'passed', 'aperture_ray_coverage':'passed'}}
    write_json(out/'metadata'/f'{name}.json',meta)
    return {'sample_id':name, 'seed':p['seed'], 'attempt':p['attempt'], 'digit_count':p['digit_count'],
            'requested_angle_deg':p['requested_angle_deg'], 'measured_angles_deg':p['measured_obb_angles_deg']}


def main():
    import bpy
    from digitgen.scene import create_scene
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',default='configs/preview.json')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--count',type=int)
    parser.add_argument('--index',type=int,help='Render a single original batch index')
    parser.add_argument('--replay',type=Path,help='Replay exact metadata config and sampled parameters')
    parser.add_argument('--rolling-preview',action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    replay = json.loads(args.replay.read_text()) if args.replay else None
    if replay and replay.get('schema_version')!=2:
        raise ValueError('This UV-textured mechanical generator replays schema 2 metadata; schema 1 belongs to the earlier curved-mesh baseline.')
    c = copy.deepcopy(replay['config']) if replay else load_config(ROOT/args.config)
    if args.count is not None:
        c['count'] = args.count
    validate_config(c)
    if args.index is not None and not 0<=args.index<c['count']:
        raise ValueError('--index must refer to an original index in [0, count)')
    out = (args.output or ROOT/c['output']).resolve()
    # Refuse nonempty output to avoid stale image/label pairs or overwriting user data.
    if out.exists() and any(out.iterdir()):
        raise ValueError(f'Output must be new or empty: {out}')
    for directory in ('images','raw_images','labels','metadata','overlays','validation'):
        (out/directory).mkdir(parents=True,exist_ok=True)
    write_json(out/'config.resolved.json',c)
    write_json(out/'classes.json',{'0':'digit_slot'})
    records, failures = [], []
    if args.rolling_preview:
        p = sample_parameters(c,0)
        middle = p['digit_count']//2
        p['wheels'][middle] = wheel_state(middle,3,0)
        scene, boxes, boundaries = create_scene(c,p)
        for name, digit, progress in [('stable_3',3,0),('early_3_to_4',3,.25),('mid_3_to_4',3,.5),
                                      ('late_3_to_4',3,.75),('stable_4',4,0),('wrap_9_to_0',9,.5)]:
            state = wheel_state(middle,digit,progress)
            state.update({k:p['wheels'][middle][k] for k in ('center_x','red')})
            p['wheels'][middle] = state
            p['digit_sequence'] = ''.join(str(w['digit']) for w in p['wheels'])
            p['rolling_preview_wheel_index'] = middle
            bpy.data.objects[f'wheel_{middle}_axle'].rotation_euler.x = state['wheel_rotation']
            bpy.context.view_layer.update()
            records.append(export_sample(out,name,c,p,boxes,boundaries,scene))
            print('SAMPLE_OK',name,flush=True)
    else:
        indices = [replay['parameters']['index']] if replay else ([args.index] if args.index is not None else range(c['count']))
        for index in indices:
            for attempt in range(1 if replay else c['max_attempts']):
                name = f'{index:06d}'
                try:
                    p = copy.deepcopy(replay['parameters']) if replay else sample_parameters(c,index,attempt)
                    scene, boxes, boundaries = create_scene(c,p)
                    record = export_sample(out,name,c,p,boxes,boundaries,scene)
                except Exception as exc:
                    failures.append({'index':index,'attempt':attempt,'seed':c['seed']+index*100003+attempt*1000000007,'reason':str(exc)})
                    write_json(out/'validation'/'failures.json',failures)
                    print('SAMPLE_REJECTED',index,attempt,str(exc),flush=True)
                    traceback.print_exc()
                    # Remove incomplete artifacts from a rejected render/export.
                    for folder,extension in [('images','png'),('raw_images','png'),('labels','txt'),('metadata','json'),('overlays','svg')]:
                        (out/folder/f'{name}.{extension}').unlink(missing_ok=True)
                    if replay:
                        raise
                    continue
                records.append(record)
                write_json(out/'manifest.json',{'samples':records,'rejections':failures})
                print('SAMPLE_OK',name,flush=True)
                break
            else:
                raise RuntimeError(f'Failed to produce index {index}; see validation/failures.json')
    angles = [a for rec in records for a in rec['measured_angles_deg']]
    summary = {'successful_images':len(records), 'rejected_attempts':len(failures),
               'positive_images':sum(r['requested_angle_deg']>0 for r in records),
               'negative_images':sum(r['requested_angle_deg']<0 for r in records),
               'five_digit_images':sum(r['digit_count']==5 for r in records),
               'six_digit_images':sum(r['digit_count']==6 for r in records),
               'measured_angle_range_deg':[min(angles),max(angles)],
               'max_target_error_deg':max(abs(a-r['requested_angle_deg']) for r in records for a in r['measured_angles_deg']),
               'source_sha256':code_hash(), 'blender_version':bpy.app.version_string,
               'status':'rendered_and_geometry_validated',
               'next_check':'Run python3 validate.py OUTPUT for independent saved-file audit and PNG contact sheets'}
    write_json(out/'manifest.json',{'samples':records,'rejections':failures})
    write_json(out/'validation'/'render_summary.json',summary)
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    main()
