"""Build a seamless cylindrical ink mask with an openly licensed font (host Python)."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent


def prepare(config):
    from font_candidates import resolve_config
    config = resolve_config(config)
    t = config['typography']
    font_path = ROOT/t['font']
    key = hashlib.sha256(font_path.read_bytes()+json.dumps(t,sort_keys=True).encode()).hexdigest()[:16]
    destination = ROOT/'assets/atlases'/f'ink_{key}.png'
    destination.parent.mkdir(parents=True,exist_ok=True)
    identity=ImageFont.truetype(str(font_path),100).getname()
    if 'font_family' in t and t['font_family'].casefold()!=identity[0].casefold():
        raise ValueError(f'Configured font family does not match actual file: {identity}')
    if 'font_weight' in t and t['font_weight'].casefold()!=identity[1].casefold():
        raise ValueError(f'Configured font weight does not match actual file: {identity}')
    if not destination.exists():
        segment, axial = t['segment_pixels'], t['axial_pixels']
        atlas = Image.new('L',(10*segment,axial))
        font = ImageFont.truetype(str(font_path),axial*2)
        glyphs = []
        for digit in range(10):
            bounds = font.getbbox(str(digit))
            glyph = Image.new('L',(bounds[2]-bounds[0],bounds[3]-bounds[1]))
            ImageDraw.Draw(glyph).text((-bounds[0],-bounds[1]),str(digit),font=font,fill=255)
            glyphs.append(glyph)
        max_width = max(g.width for g in glyphs)
        for digit,glyph in enumerate(glyphs):
            width = max(1,round(axial*t['numeral_width']*t.get('glyph_width_scale',1)*glyph.width/max_width))
            height = max(1,round(segment*t['numeral_height']*t.get('glyph_height_scale',1)))
            glyph = glyph.resize((width,height),Image.Resampling.LANCZOS)
            face = Image.new('L',(axial,segment))
            horizontal=t.get('glyph_horizontal_alignment','center')
            vertical=t.get('glyph_vertical_alignment','center')
            xpos={'left':0,'center':(axial-width)//2,'right':axial-width}[horizontal]
            ypos={'top':0,'center':(segment-height)//2,'bottom':segment-height}[vertical]
            face.paste(glyph,(xpos,ypos))
            # u grows with cylinder +angle (up); v grows with local +X (right).
            # PNG y is downward: transpose about the anti-diagonal, not rotate.
            tile = face.transpose(Image.Transpose.TRANSVERSE)
            atlas.paste(tile,(digit*segment,0))
        atlas.save(destination)
    manifest = {'path':str(destination.relative_to(ROOT)), 'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
                'font':t['font'],'font_sha256':hashlib.sha256(font_path.read_bytes()).hexdigest(),
                'size':[10*t['segment_pixels'],t['axial_pixels']], 'typography':t,
                'uv_definition':'u=angle/(2*pi)+0.05, v=x/wheel_width+0.5; repeat u',
                'license':t.get('font_license','assets/fonts/OFL.txt')}
    (ROOT/'assets/atlases/current.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__=='__main__':
    from digitgen.config import load_config
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='configs/preview.json')
    from font_candidates import PRESETS, resolve_config
    parser.add_argument('--font-preset', choices=sorted(PRESETS))
    args = parser.parse_args()
    print(json.dumps(prepare(resolve_config(load_config(ROOT/args.config), args.font_preset)),indent=2))
