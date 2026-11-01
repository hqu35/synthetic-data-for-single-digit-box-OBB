import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def verify_spec(spec):
    inputs=[(spec['path'],'sha256')]
    if 'source_image' in spec:inputs.append((spec['source_image'],'source_image_sha256'))
    else:inputs.append((spec['font'],'font_sha256'))
    for path,field in inputs:
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=spec[field]:
            raise ValueError(f'Asset checksum differs from recorded sample: {path}')


def texture_spec(c):
    from font_candidates import resolve_config
    c=resolve_config(c)
    t=c['typography']
    if t.get('image_source'):
        from .photo_atlas import photo_key
        source=ROOT/t['image_source'];path=ROOT/'assets/atlases'/f'photo_{photo_key(t)}.png'
        if not path.exists():raise ValueError('Missing photo atlas; run prepare_assets.py for this configuration')
        return {'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'source_image':t['image_source'],'source_image_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                'uv_definition':'u=angle/(2*pi)+0.05, v=x/wheel_width+0.5; repeat u',
                'size':[10*t['segment_pixels'],t['axial_pixels']]}
    font=ROOT/t['font']
    key=hashlib.sha256(font.read_bytes()+json.dumps(t,sort_keys=True).encode()).hexdigest()[:16]
    path=ROOT/'assets/atlases'/f'ink_{key}.png'
    if not path.exists():
        raise ValueError('Missing ink atlas. Run python3 prepare_assets.py --config YOUR_CONFIG before native Blender execution.')
    return {'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'font':t['font'],'font_sha256':hashlib.sha256(font.read_bytes()).hexdigest(),
            'uv_definition':'u=angle/(2*pi)+0.05, v=x/wheel_width+0.5; repeat u',
            'size':[10*t['segment_pixels'],t['axial_pixels']]}
