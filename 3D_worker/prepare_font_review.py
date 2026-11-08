"""Prepare industrial font review configs, UV atlases, and upright review sheets."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
from font_candidates import PRESETS, resolve_config
from prepare_assets import prepare
from digitgen.assets import texture_spec
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs/industrial_fonts_review'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    config=json.loads((ROOT/'configs/stage1_final_refinement.json').read_text())
    entries={}
    for name in PRESETS:
        c=resolve_config(config,name)
        manifest=prepare(c)
        assert texture_spec(c)['sha256']==manifest['sha256']
        (OUT/f'{name}_config.json').write_text(json.dumps(c,indent=2)+'\n')
        (OUT/f'{name}_atlas_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        atlas=Image.open(ROOT/manifest['path'])
        atlas.save(OUT/f'{name}_cylindrical_mask.png')
        # Undo exactly the cylinder UV transpose; retain the original cell fill.
        tiles=[];segment=c['typography']['segment_pixels'];axial=c['typography']['axial_pixels']
        for d in range(10):
            tile=atlas.crop((d*segment,0,(d+1)*segment,axial)).transpose(Image.Transpose.TRANSVERSE)
            tiles.append(tile)
        sheet=Image.new('RGB',(2560,340),(237,234,220));draw=ImageDraw.Draw(sheet)
        draw.text((16,8),name+' | '+PRESETS[name]['description'],fill=(20,20,20))
        for d,tile in enumerate(tiles):
            face=Image.new('RGB',tile.size,(237,234,220));face.paste((5,6,7),(0,0,*tile.size),tile)
            sheet.paste(face.resize((256,256),Image.Resampling.LANCZOS),(d*256,48))
            draw.text((d*256+122,318),str(d),fill=(20,20,20))
        sheet.save(OUT/f'{name}_upright_0-9.png')
        entries[name]={'description':PRESETS[name]['description'],'atlas':manifest}
    (OUT/'font_preparation.json').write_text(json.dumps(entries,indent=2)+'\n')
    print(json.dumps({k:v['atlas']['path'] for k,v in entries.items()},indent=2))

if __name__=='__main__':main()
