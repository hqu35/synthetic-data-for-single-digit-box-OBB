"""Validate the finished 20-image scratch batch and build an overview."""
from collections import Counter
from pathlib import Path
import hashlib,json,math
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;p=ROOT/'outputs/scratch_multi_version'
status=json.loads((p/'status.json').read_text());assert status['state']=='complete' and status['completed']==20
metas=sorted((p/'metadata').glob('*.json'));images=sorted((p/'images').glob('*.png'));labels=sorted((p/'labels').glob('*.txt'));assert len(metas)==len(images)==len(labels)==20
lights=Counter();scratches=Counter();seeds=set();scratch_seeds=set();sequences=set();all_digits=set();angles=[];yaws=[];res=[];sha=set();transitions=0
for f in metas:
 m=json.loads(f.read_text());name=f.stem;image=p/'images'/f'{name}.png';label=p/'labels'/f'{name}.txt';raw=label.read_text().splitlines();assert len(raw)==5
 for line in raw:
  parts=line.split();assert len(parts)==9 and parts[0]=='0';coords=[float(x) for x in parts[1:]];assert all(math.isfinite(x) and 0<=x<=1 for x in coords)
 assert hashlib.sha256(image.read_bytes()).hexdigest()==m['image_sha256'];assert hashlib.sha256(label.read_bytes()).hexdigest()==m['label_sha256']
 with Image.open(image) as im:assert list(im.size)==m['resolution'];im.verify()
 assert len(m['digits'])==len(set(m['digits']))==5 and m['digits'].isdigit();sequences.add(m['digits']);all_digits.update(m['digits'])
 seed=m['parameters']['seed'];seeds.add(seed);scratch_seeds.add(m['scratch']['seed']);lights[m['light_style']]+=1;scratches[m['scratch']['name']]+=1
 assert m['parameters']['lighting']['preset']==m['light_style'];assert abs(m['theta_deg'])<40 and abs(m['yaw_deg'])<=8
 assert abs(m['theta_deg']-m['parameters']['camera']['pitch_deg'])<1e-8 and abs(m['yaw_deg']-m['parameters']['camera']['yaw_deg'])<1e-8
 assert .90<=m['framing']['register_area_fraction']<=.95
 angles.append(m['theta_deg']);yaws.append(m['yaw_deg']);res.append(tuple(m['resolution']));sha.add(m['image_sha256']);transitions+=any(t>0 for t in m['transitions'])
assert len(sequences)==len(seeds)==len(scratch_seeds)==len(sha)==20 and all_digits==set('0123456789')
assert lights==Counter({'blue':4,'white':4,'natural':4,'pale_blue':4,'vintage_beige':4}) and scratches==Counter({'heavy':12,'medium':6,'light':2})
report={'status':'passed','count':20,'unique_digit_sequences':len(sequences),'unique_digits_per_image':5,'digit_coverage':''.join(sorted(all_digits)),
 'unique_render_seeds':len(seeds),'unique_scratch_seeds':len(scratch_seeds),'lighting_counts':dict(lights),'scratch_counts':dict(scratches),
 'theta_definition':'signed camera pitch degrees','theta_range_deg':[min(angles),max(angles)],'yaw_range_deg':[min(yaws),max(yaws)],
 'resolutions':[list(x) for x in sorted(set(res))],'samples_with_transitions':transitions,'labels':'five in-frame normalized class-0 OBBs per image',
 'limitations':'Geometric labels are not corrected for glass refraction; OBB validity does not certify legibility or scratch realism.'}
(p/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
board=Image.new('RGB',(2000,1200),'white');draw=ImageDraw.Draw(board)
for i,f in enumerate(metas):
 m=json.loads(f.read_text());x=(i%4)*500;y=(i//4)*240;im=Image.open(p/'images'/f'{f.stem}.png').convert('RGB');im.thumbnail((490,182),Image.Resampling.LANCZOS);board.paste(im,(x+(500-im.width)//2,y+46))
 draw.text((x+5,y+4),f"{f.stem}   digits {m['digits']}   {m['scratch']['name']}",font=font,fill='black')
 draw.text((x+5,y+25),f"{m['light_style']}  |  theta {m['theta_deg']:+.1f}°  |  yaw {m['yaw_deg']:+.1f}°",font=small,fill='black')
board.save(p/'contact_sheet.png')
print(json.dumps(report,indent=2))
