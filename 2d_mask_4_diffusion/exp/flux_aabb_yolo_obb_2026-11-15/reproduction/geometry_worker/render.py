"""Render conditioning images and separate diagnostic overlays."""
import math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont


def make_images(data):
    w,h=data['resolution'];scale=2
    image=Image.new('L',(w*scale,h*scale),data['background_gray']);draw=ImageDraw.Draw(image)
    for strip in data['strips']:
        poly=[(round(x*scale),round(y*scale)) for x,y in strip['contour_px']]
        draw.polygon(poly,fill=strip['fill_gray'])
    conditioning=image.resize((w,h),Image.Resampling.LANCZOS).convert('RGB')
    preview=conditioning.copy();draw=ImageDraw.Draw(preview)
    try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
    except OSError:font=ImageFont.load_default()
    for strip in data['strips']:
        poly=[tuple(p) for p in strip['contour_px']]
        if data.get('schema_version',1)>=3:
            top,left,bottom,right=strip['flux_bbox'];box=[(left*w/1000,top*h/1000),(right*w/1000,top*h/1000),(right*w/1000,bottom*h/1000),(left*w/1000,bottom*h/1000)]
        elif data.get('schema_version',1)>=2:
            x0,y0,x1,y1=strip['aabb_px'];box=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        else:box=[tuple(p) for p in strip['obb_px']]
        draw.line(poly+[poly[0]],fill=(38,241,113),width=2)
        draw.line(box+[box[0]],fill=(255,176,40),width=2)
        for x,y in box:draw.ellipse((x-3,y-3,x+3,y+3),fill=(255,86,80))
        x,y=box[0];draw.text((x+4,y+4),str(strip['index']),fill=(255,255,255),stroke_width=2,stroke_fill=(0,0,0),font=font)
    return conditioning,preview


def save_sample(data,out):
    import json
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    image,preview=make_images(data);image.save(out/'conditioning.png');preview.save(out/'preview.png')
    if data.get('schema_version',1)==2:
        rows=('0 '+' '.join(f'{v:.10f}' for v in s['aabb_normalized'])+'\n' for s in data['strips'])
    else:rows=('0 '+' '.join(f'{v:.10f}' for p in s['obb_normalized'] for v in p)+'\n' for s in data['strips'])
    (out/'annotations.txt').write_text(''.join(rows))
    if data.get('schema_version',1)==2:
        (out/'aabb.json').write_text(json.dumps({'coordinate_order':'xmin,ymin,xmax,ymax','normalized_to':'full_image','boxes':[s['aabb_normalized'] for s in data['strips']]},indent=2,allow_nan=False)+'\n')
    if data.get('schema_version',1)>=3:
        (out/'flux_bboxes.json').write_text(json.dumps({'coordinate_order':'top,left,bottom,right','coordinate_range':[0,1000],'normalized_to':'full_image','boxes':[s['flux_bbox'] for s in data['strips']]},indent=2,allow_nan=False)+'\n')
    (out/'geometry.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')


def make_contact_sheet(samples,path,filename='preview.png'):
    width=1500;cell_w=500;cell_h=245
    sheet=Image.new('RGB',(width,math.ceil(len(samples)/3)*cell_h),'white');draw=ImageDraw.Draw(sheet)
    try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)
    except OSError:font=ImageFont.load_default()
    for i,sample in enumerate(samples):
        x=(i%3)*cell_w;y=(i//3)*cell_h;im=Image.open(Path(sample)/filename).convert('RGB');im.thumbnail((490,200),Image.Resampling.LANCZOS)
        label='  |  green: contour   orange: AABB' if filename=='preview.png' else '  |  conditioning'
        sheet.paste(im,(x+(cell_w-im.width)//2,y+37));draw.text((x+8,y+8),Path(sample).name+label,fill=(20,25,30),font=font)
    sheet.save(path)
