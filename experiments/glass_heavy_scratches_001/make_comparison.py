"""Create a clean-versus-heavy sheet with native views and matching closeups."""
import argparse
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--input',default=str(HERE/'results'));p=Path(parser.parse_args().input)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',23);sheet=Image.new('RGB',(1970,1010),'white');draw=ImageDraw.Draw(sheet);(p/'closeups').mkdir(exist_ok=True)
for i,(name,label) in enumerate([('01_clean_baseline','Clean baseline'),('02_heavy_scratches','Heavy scratches')]):
 im=Image.open(p/'images'/f'{name}.png').convert('RGB');crop=im.crop((370,105,730,335));crop.save(p/'closeups'/f'{name}.png');y=i*505
 draw.text((12,y+5),f'{label}   |   full image at 1200 × 460',font=font,fill='black');draw.text((1238,y+5),'same glass crop, 2×',font=font,fill='black');sheet.paste(im,(0,y+36));sheet.paste(crop.resize((720,460),Image.Resampling.NEAREST),(1235,y+36))
sheet.save(p/'comparison_sheet.png');print(p/'comparison_sheet.png')
