"""Independent saved-artifact audit and PNG overlays. Requires Pillow."""
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageStat
from digitgen.export import read_labels, write_json
from digitgen.geometry import validate_boxes
from collections import Counter


def audit(root):
    root = Path(root).resolve()
    manifest = json.loads((root/'manifest.json').read_text())
    expected = {r['sample_id'] for r in manifest['samples']}
    if not expected:
        raise ValueError('Empty dataset')
    for folder, ext in [('images','png'),('labels','txt'),('metadata','json'),('overlays','svg')]:
        actual = {p.stem for p in (root/folder).glob('*.'+ext)}
        if actual != expected:
            raise ValueError(f'Missing or unexpected {folder}: {actual ^ expected}')
    records, thumbs, parameters = [], [], []
    for name in sorted(expected):
        meta = json.loads((root/'metadata'/f'{name}.json').read_text())
        p, c = meta['parameters'], meta['config']
        parameters.append(p)
        resolution = meta['resolution']
        with Image.open(root/'images'/f'{name}.png') as loaded:
            loaded.load()
            if loaded.format!='PNG' or list(loaded.size)!=resolution:
                raise ValueError(f'Invalid rendered image {name}')
            image = loaded.convert('RGB')
        boxes = read_labels(root/'labels'/f'{name}.txt',resolution)
        if len(boxes)!=p['digit_count'] or len(p['wheels'])!=p['digit_count']:
            raise ValueError(f'Incorrect box count {name}')
        angles = validate_boxes(boxes,meta['projected_boundaries_px'],resolution,p['requested_angle_deg'],c['rotation'])
        if any(abs(x-y)>1e-5 for b,stored in zip(boxes,meta['obb_corners_px']) for point,spoint in zip(b,stored) for x,y in zip(point,spoint)):
            raise ValueError(f'Metadata/export mismatch {name}')
        if not math.isclose(p['pitch'],p['slot_width']*(1+p['gap_ratio'])) or not p['wheel_width']<p['pitch']:
            raise ValueError('Invalid physical gap/pitch')
        if meta['schema_version']>=2:
            mech=p['mechanics']
            if mech['assembly_width']+mech['wheel_axial_clearance']>p['pitch']+1e-8:
                raise ValueError('Pins/rims collide with adjacent wheel assembly')
            if mech['pin_count']!=(10*mech['pins_per_digit_interval'] if mech['pins_enabled'] else 0):
                raise ValueError('Incorrect side-pin count')
            photo=p['photograph']
            if photo['final_dimensions']!=resolution or photo['geometry_transform']!='identity' or photo['clipped_channel_fraction']>.03:
                raise ValueError('Invalid camera appearance geometry/clipping')
            with Image.open(root/'raw_images'/f'{name}.png') as raw:
                if list(raw.size)!=resolution:raise ValueError('Raw/final resolution mismatch')
            import hashlib
            asset=Path(__file__).resolve().parent/p['texture']['path']
            if hashlib.sha256(asset.read_bytes()).hexdigest()!=p['texture']['sha256']:
                raise ValueError('Ink texture asset no longer matches metadata')
        stddevs = []
        for state, boundary in zip(p['wheels'],meta['projected_boundaries_px']):
            if not 0<=state['digit']<=9 or not 0<=state['transition_progress']<1:
                raise ValueError('Invalid rolling state')
            if not math.isclose(state['wheel_rotation'],(state['digit']+state['transition_progress'])*2*math.pi/10):
                raise ValueError('Incorrect physical wheel rotation')
            mask = Image.new('L', image.size)
            ImageDraw.Draw(mask).polygon([tuple(pt) for pt in boundary],fill=255)
            deviation = ImageStat.Stat(image.convert('L'),mask).stddev[0]
            if deviation<3:
                raise ValueError(f'Blank/low-contrast aperture {name}:{state["index"]}')
            stddevs.append(deviation)
        overlay = image.copy()
        draw = ImageDraw.Draw(overlay)
        for i,box in enumerate(boxes):
            points = [tuple(pt) for pt in box]
            draw.line(points+[points[0]], fill=(35,255,100),width=2)
            x,y = points[0]
            draw.ellipse((x-2,y-2,x+2,y+2),fill=(255,180,30))
            draw.text((x+3,y-12),str(i),fill=(0,255,80))
        overlay.save(root/'overlays'/f'{name}.png')
        thumb = overlay.copy()
        thumb.thumbnail((320,160))
        tile = Image.new('RGB',(320,182),(26,28,32))
        tile.paste(thumb,((320-thumb.width)//2,0))
        ImageDraw.Draw(tile).text((6,164),f'{name} | {p["requested_angle_deg"]:+.2f} deg',fill='white')
        thumbs.append(tile)
        records.append({'id':name,'angles_deg':angles,'slot_contrast_stddev':stddevs})
    cols = min(5,len(thumbs))
    sheet = Image.new('RGB',(cols*320,math.ceil(len(thumbs)/cols)*182),(26,28,32))
    for i,tile in enumerate(thumbs):
        sheet.paste(tile,((i%cols)*320,(i//cols)*182))
    sheet.save(root/'validation'/'contact_sheet.png')
    # Rolling preview compares the unchanged scene and exact exported boxes.
    rolling = []
    for name in expected:
        meta = json.loads((root/'metadata'/f'{name}.json').read_text())
        if 'rolling_preview_wheel_index' in meta['parameters']:
            rolling.append(meta)
    if rolling:
        reference = rolling[0]
        for meta in rolling[1:]:
            for field in ('camera','lighting','appearance','aperture_world_boundaries'):
                if meta['parameters'][field]!=reference['parameters'][field]:
                    raise ValueError(f'Rolling preview scene changed: {field}')
            if meta['obb_corners_px']!=reference['obb_corners_px']:
                raise ValueError('Rolling preview boxes changed with wheel rotation')
        # Crop only the varying wheel, in requested temporal order, without rectification.
        names = ['stable_3','early_3_to_4','mid_3_to_4','late_3_to_4','stable_4','wrap_9_to_0']
        film = Image.new('RGB',(6*180,250),(26,28,32))
        for i,name in enumerate(names):
            meta = json.loads((root/'metadata'/f'{name}.json').read_text())
            index = meta['parameters']['rolling_preview_wheel_index']
            box = meta['obb_corners_px'][index]
            bounds = (math.floor(min(x for x,y in box))-5, math.floor(min(y for x,y in box))-5,
                      math.ceil(max(x for x,y in box))+5, math.ceil(max(y for x,y in box))+5)
            with Image.open(root/'overlays'/f'{name}.png') as im:
                crop = im.crop(bounds)
                crop.thumbnail((170,210))
                film.paste(crop,(i*180+(180-crop.width)//2,0))
            ImageDraw.Draw(film).text((i*180+4,222),name,fill='white')
        film.save(root/'validation'/'rolling_sequence.png')
    summary = json.loads((root/'validation'/'render_summary.json').read_text())
    summary.update({'status':'passed_saved_artifact_audit','audited_images':len(records),
                    'audited_boxes':sum(len(r['angles_deg']) for r in records),
                    'rolling_box_invariance': bool(rolling), 'per_sample_checks':records,
                    'limitations':'Ray coverage and image contrast are automated checks; visual appearance requires human review.'})
    summary['distribution']={
        'target_signs':dict(Counter('positive' if p['requested_angle_deg']>0 else 'negative' for p in parameters)),
        'digit_counts':dict(Counter(p['digit_count'] for p in parameters)),
        'gap_ratios':[p['gap_ratio'] for p in parameters],
        'absolute_angle_range_deg':[min(abs(a) for r in records for a in r['angles_deg']),max(abs(a) for r in records for a in r['angles_deg'])],
        'states':dict(Counter('transition' if w['transition'] else 'stable' for p in parameters for w in p['wheels']))}
    if 'photograph' in parameters[0]:
        summary['distribution'].update({'camera_presets':dict(Counter(p['photograph']['preset'] for p in parameters)),
                                        'pins_per_interval':dict(Counter(p['mechanics']['pins_per_digit_interval'] for p in parameters))})
    summary['next_check']='Inspect the final contact sheet and representative RGB/overlay images.'
    write_json(root/'validation'/'summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='per_sample_checks'},indent=2))
    return summary


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    audit(parser.parse_args().output)
