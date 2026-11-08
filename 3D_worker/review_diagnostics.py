"""Audit diagnostic labels and create comparable material/camera/UV sheets."""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
from validate import audit
from digitgen.export import write_json


def comparison(root,names,destination):
    sheet=Image.new('RGB',(512*len(names),280),(24,26,30))
    for i,name in enumerate(names):
        with Image.open(root/'images'/f'{name}.png') as source:
            source=source.convert('RGB');source.thumbnail((512,256))
            sheet.paste(source,(i*512,0))
        ImageDraw.Draw(sheet).text((i*512+8,260),name,fill='white')
    sheet.save(destination)


def review(root):
    root=Path(root)
    for name in ('materials','uv_calibration','camera_casts'):audit(root/name)
    comparison(root/'materials',['basic','reference_dark_plastic','meter_cream_matte'],root/'material_comparison.png')
    comparison(root/'camera_casts',['neutral','cool_blue','warm'],root/'camera_comparison.png')
    comparison(root/'uv_calibration',['digits_0_to_4','digits_5_to_9'],root/'uv_calibration.png')
    records=[json.loads(p.read_text()) for p in sorted((root/'materials/metadata').glob('*.json'))]
    reference=records[0]
    for record in records[1:]:
        for key in ('camera','lighting','mechanics','wheels'):
            if record['parameters'][key]!=reference['parameters'][key]:raise ValueError(f'Material comparison changed {key}')
        if record['obb_corners_px']!=reference['obb_corners_px']:raise ValueError('Material comparison geometry changed')
    records=[json.loads(p.read_text()) for p in sorted((root/'camera_casts/metadata').glob('*.json'))]
    reference=records[0]
    for record in records[1:]:
        for key in ('camera','lighting','appearance','mechanics','wheels'):
            if record['parameters'][key]!=reference['parameters'][key]:raise ValueError(f'Camera comparison changed physical {key}')
        if record['obb_corners_px']!=reference['obb_corners_px']:raise ValueError('Camera effects changed annotation geometry')
    raw=[Image.open(root/'camera_casts/raw_images'/f'{name}.png').convert('RGB') for name in ['neutral','cool_blue','warm']]
    identical=all(ImageChops.difference(raw[0],im).getbbox() is None for im in raw[1:])
    differences=[ImageChops.difference(raw[0],im) for im in raw[1:]]
    maximum=max(max(high for low,high in diff.getextrema()) for diff in differences)
    changed=max(sum(pixel!=(0,0,0) for pixel in diff.getdata()) for diff in differences)
    # Multi-threaded Cycles/denoiser can change a few rounding decisions by 1 LSB.
    # Scene-parameter identity is exact; report renderer variation separately.
    if maximum>1:raise ValueError('Unexpected physical-render difference during camera-only comparison')
    write_json(root/'comparison_checks.json',{'status':'passed','same_scene_material_comparison':True,
               'same_physical_scene_camera_comparison':True,'camera_comparison_raw_rgb_identical':identical,
               'maximum_raw_8bit_channel_difference':maximum,'maximum_raw_changed_pixels':changed,
               'uv_stable_digits_rendered':list(range(10)),
               'note':'Inspect sheets for appearance; numeric invariance is not a photorealism assessment.'})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    review(parser.parse_args().output)
