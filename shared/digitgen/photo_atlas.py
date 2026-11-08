"""Extract the user's photographed numerals into the wheel's repeating ink atlas."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def photo_key(t):
    source=ROOT/t['image_source']
    return hashlib.sha256(source.read_bytes()+json.dumps(t,sort_keys=True).encode()).hexdigest()[:16]

def build_photo_atlas(config):
    import numpy as np
    from PIL import Image
    t=config['typography'];source=ROOT/t['image_source'];segment=t['segment_pixels'];axial=t['axial_pixels']
    pixels=np.asarray(Image.open(source).convert('L'));bounds=t['source_row_boundaries'];x0,x1=t['source_crop_x']
    if len(bounds)!=11 or any(a>=b for a,b in zip(bounds,bounds[1:])):raise ValueError('Need ten ordered digit crops')
    glyphs=[];measurements=[]
    for digit,(a,b) in enumerate(zip(bounds,bounds[1:])):
        # Remove strip separators; a few near-black seam pixels otherwise look
        # like floating ink above digit 4 in the supplied source.
        a+=8;b-=1
        crop=pixels[a:b,x0:x1];ink=np.clip((155.0-crop.astype(np.float32))/90,0,1)
        yy,xx=np.where(ink>.4)
        if not len(xx):raise ValueError(f'Digit {digit} has no ink')
        # Crop the glyph itself; white dividers and gray photographed substrate
        # are intentionally excluded so the physical material remains procedural.
        left=max(0,int(xx.min())-2);right=min(ink.shape[1],int(xx.max())+3)
        top=max(0,int(yy.min())-2);bottom=min(ink.shape[0],int(yy.max())+3)
        glyph=Image.fromarray(np.rint(255*ink[top:bottom,left:right]).astype('uint8'),'L')
        glyphs.append(glyph);measurements.append({'digit':digit,'source_box':[x0+left,a+top,x0+right,a+bottom]})
    max_width=max(g.width for g in glyphs);atlas=Image.new('L',(10*segment,axial))
    order=t.get('tile_order',list(range(10)))
    if sorted(order)!=list(range(10)):raise ValueError('tile_order must be a permutation of digits 0 to 9')
    for digit,glyph in enumerate(glyphs):
        width=max(1,round(axial*t['numeral_width']*glyph.width/max_width));height=round(segment*t['numeral_height'])
        glyph=glyph.resize((width,height),Image.Resampling.LANCZOS);face=Image.new('L',(axial,segment))
        face.paste(glyph,((axial-width)//2,(segment-height)//2))
        atlas.paste(face.transpose(Image.Transpose.TRANSVERSE),(order.index(digit)*segment,0))
    path=ROOT/'assets/atlases'/f'photo_{photo_key(t)}.png';path.parent.mkdir(parents=True,exist_ok=True);atlas.save(path)
    return path,measurements
