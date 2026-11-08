"""Build a labeled sheet with native full views and enlarged matching crops."""
import argparse
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',default=str(HERE/'results_refined'));out=Path(parser.parse_args().input)
names=[('01_baseline','Baseline'),('02_light_scratches','Light scratches'),('03_moderate_scratches','Moderate scratches'),('04_surface_noise','Surface noise only'),('05_combined','Combined')]
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',23)
board=Image.new('RGB',(1970,5*505),'white');draw=ImageDraw.Draw(board);(out/'closeups').mkdir(exist_ok=True)
for i,(name,label) in enumerate(names):
 im=Image.open(out/'images'/f'{name}.png').convert('RGB');crop=im.crop((370,105,730,335));crop.save(out/'closeups'/f'{name}.png')
 y=i*505;draw.text((12,y+5),f'{label}   |   full image at 1200 × 460',font=font,fill='black');draw.text((1238,y+5),'same glass crop, 2×',font=font,fill='black')
 board.paste(im,(0,y+36));board.paste(crop.resize((720,460),Image.Resampling.NEAREST),(1235,y+36))
board.save(out/'comparison_sheet.png')
print(out/'comparison_sheet.png')
