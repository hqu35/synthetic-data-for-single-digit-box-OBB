"""Build a mask-scale ink atlas from rectified photographed characters."""

import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GUIDE = ROOT / '2D_Mask_for_Diffusion/exp/Flux_3_graphics_guidance_annotation'
MASK = next(ROOT.glob('Flux*/Prompt_generator/Prompt_Generator_EXP_ComfyUI_2026-11-16/mask'))
OUT = HERE / 'exp/2026-11-17_manual_atlas'
LABELS = '0800920004'


def read(path):
    return json.loads(path.read_text())


def coverage(image):
    values = np.asarray(image.convert('L'), dtype=float)
    dark, light = np.percentile(values, [5, 85])
    light -= 0.24 * (light - dark)
    opacity = np.clip((light - values) / (light - dark), 0, 1)
    return Image.fromarray(np.uint8(255 * opacity))


def annotated(record):
    corners = record['tight_character_obb']
    points = sum((corners[key] for key in ('tl','bl','br','tr')), [])
    measurements = record['measurements']
    size = tuple(round(measurements[f'character_{axis}_px'])
                 for axis in ('width', 'height'))
    image = Image.open(GUIDE / 'images' / record['image'])
    crop = image.transform(size, Image.Transform.QUAD, points, Image.Resampling.BICUBIC)
    return coverage(crop)


def main():
    records = read(OUT / 'latest.json')['annotations']
    groups = {}
    for digit, record in zip(LABELS, records):
        groups.setdefault(digit, []).append(record)
    groups['1'] = [read(OUT / 'earlier.json')['annotations'][0]]
    geometry = read(MASK / 'geometry.json')
    strips = geometry['strips']
    sizes = [[2 * np.linalg.norm(strip['coefficients_px'][axis])
              for axis in ('a','b')] for strip in strips]
    width, height = np.rint(np.median(sizes, axis=0)).astype(int)
    ratios = [record['ratios'] for record in records]
    width_key = 'character_width_to_digit_width'
    height_key = 'character_height_to_digit_height'
    ink_height = np.median([item[height_key] for item in ratios])
    gap_ratio = np.median([item['gap_to_character_height'] for item in ratios])
    pitch = round(height * ink_height * (1 + gap_ratio))
    atlas = Image.new('L', (width, pitch * 10))
    config = read(ROOT / 'shared/configs/rolling_numerals_atlas.json')['typography']
    reference = Image.open(ROOT / 'shared' / config['image_source'])
    bounds = config['source_row_boundaries']
    left, right = config['source_crop_x']
    shapes = []
    for digit in range(10):
        crop = reference.crop((left,bounds[digit]+8,right,bounds[digit+1]-1))
        glyph = coverage(crop)
        shapes.append(glyph.crop(glyph.point(lambda value: 255*(value>12)).getbbox()))
    zero_width = np.median([item['ratios'][width_key] for item in groups['0']])
    provenance = {}
    for digit, shape in enumerate(shapes):
        candidates = groups.get(str(digit))
        if candidates:
            record = min(candidates, key=lambda item:
                         abs(item['ratios'][height_key] - ink_height))
            shape = annotated(record)
            relative_width = record['ratios'][width_key]
            relative_height = record['ratios'][height_key]
            source = record['image']
        else:
            relative_height = ink_height
            relative_width = zero_width * shape.width / shapes[0].width
            source = config['image_source']
        size = (min(width, round(width * relative_width)),
                min(pitch, round(height * relative_height)))
        shape = shape.resize(size, Image.Resampling.LANCZOS)
        origin = ((width-shape.width)//2, digit*pitch+(pitch-shape.height)//2)
        atlas.paste(shape, origin)
        provenance[digit] = dict(source=source, ink_box_px=size)
    rgba = Image.new('RGBA', atlas.size, (16,16,16,0))
    rgba.putalpha(atlas)
    rgba.save(OUT / 'atlas.png')
    for reading, states, name in [('01234',[0]*5,'centered_01234'),
                                  ('56789',[0]*5,'centered_56789'),
                                  ('21546',[0,.7,0,.7,0],'rolling_21546')]:
        preview = np.array(Image.open(MASK / 'conditioning.png').convert('RGB'))
        rows, cols = np.indices(preview.shape[:2])
        for digit, theta, strip in zip(reading,states,strips):
            coeff = strip['coefficients_px']
            center, across, down, bend = map(np.array,
                (coeff[key] for key in ('p','a','b','k')))
            inverse = np.linalg.inv(np.column_stack([across, down]))
            local = inverse @ np.stack([cols-center[0],rows-center[1]]).reshape(2,-1)
            horizontal, vertical = local.reshape(2,*rows.shape)
            horizontal -= (inverse @ bend)[0] * vertical**2
            inside = (abs(horizontal)<=1) & (abs(vertical)<=1)
            atlas_x = ((horizontal[inside]+1)*width/2).astype(int).clip(0,width-1)
            atlas_y = (int(digit)+theta+.5)*pitch + vertical[inside]*height/2
            alpha = np.asarray(atlas)[np.floor(atlas_y).astype(int)%atlas.height,atlas_x]
            blend = alpha[:,None].astype(float)/255
            preview[inside] = np.rint(preview[inside]*(1-blend)+16*blend)
        Image.fromarray(preview).save(OUT / f'{name}.png')
    summary = dict(mask_resolution=geometry['resolution'], strip_sizes_px=sizes,
                   median_strip_px=[int(width),int(height)], pitch_px=pitch,
                   median_height_fraction=ink_height, gap_over_ink_height=gap_ratio,
                   glyphs=provenance)
    (OUT / 'calibration.json').write_text(json.dumps(summary, indent=2)+'\n')


if __name__ == '__main__':
    main()
