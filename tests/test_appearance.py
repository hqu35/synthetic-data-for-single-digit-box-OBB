import copy
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from digitgen.camera_appearance import read_png,write_png,process_image
from digitgen.config import load_config
from digitgen.sampling import sample_parameters

ROOT=Path(__file__).resolve().parents[1]


class AppearanceTests(unittest.TestCase):
    def test_png_roundtrip_and_identity_processing(self):
        rgb=np.random.default_rng(17).integers(10,240,size=(31,43,3),dtype=np.uint8)
        params={'camera_white_balance':[1,1,1],'postprocess_color_cast':[1,1,1],'camera_exposure':0,
                'contrast':1,'blur_sigma_px':0,'sensor_noise_std':0,'noise_seed':7}
        with tempfile.TemporaryDirectory() as tmp:
            raw,final=Path(tmp)/'raw.png',Path(tmp)/'final.png'
            Image.fromarray(rgb).save(raw)
            self.assertTrue(np.array_equal(read_png(raw),rgb))
            process_image(raw,final,params)
            self.assertTrue(np.array_equal(np.asarray(Image.open(final)),rgb))
            self.assertEqual(params['final_dimensions'],[43,31])

    def test_noise_is_seeded_and_blue_cast_is_independent(self):
        c=load_config(ROOT/'configs/preview.json')
        a=sample_parameters(c,0)
        c['camera_appearance']['preset']='cool_blue'
        b=sample_parameters(c,0)
        self.assertEqual(a['appearance'],b['appearance'])
        self.assertEqual(a['lighting'],b['lighting'])
        p=copy.deepcopy(b['photograph'])
        p.update({'camera_white_balance':[1,1,1],'camera_exposure':0,'contrast':1,'blur_sigma_px':0})
        with tempfile.TemporaryDirectory() as tmp:
            raw=Path(tmp)/'raw.png';write_png(raw,np.full((20,30,3),150,dtype=np.uint8))
            paths=[Path(tmp)/f'{i}.png' for i in range(2)]
            for path in paths:process_image(raw,path,p)
            self.assertEqual(paths[0].read_bytes(),paths[1].read_bytes())
            means=read_png(paths[0]).mean(axis=(0,1))
            self.assertGreater(means[2],means[0])

    def test_uv_mask_orientation_matches_upright_font(self):
        c=load_config(ROOT/'configs/preview.json');p=sample_parameters(c,0);t=c['typography']
        atlas=np.asarray(Image.open(ROOT/p['texture']['path']))
        segment,axial=t['segment_pixels'],t['axial_pixels']
        font=ImageFont.truetype(str(ROOT/t['font']),axial*2)
        glyphs=[]
        for d in range(10):
            box=font.getbbox(str(d));im=Image.new('L',(box[2]-box[0],box[3]-box[1]))
            ImageDraw.Draw(im).text((-box[0],-box[1]),str(d),font=font,fill=255);glyphs.append(im)
        maximum=max(im.width for im in glyphs)
        for d,im in enumerate(glyphs):
            width=round(axial*t['numeral_width']*im.width/maximum);height=round(segment*t['numeral_height'])
            face=Image.new('L',(axial,segment));face.paste(im.resize((width,height),Image.Resampling.LANCZOS),((axial-width)//2,(segment-height)//2))
            # Independent surface-to-image lookup: +X -> right, +angle -> up.
            ys,xs=np.indices((segment,axial))
            reconstructed=atlas[axial-1-xs,d*segment+segment-1-ys]
            self.assertTrue(np.array_equal(reconstructed,np.asarray(face)),f'digit {d} is mirrored or inverted')
        self.assertFalse(atlas[:,0].any());self.assertFalse(atlas[:,-1].any())


if __name__=='__main__':unittest.main()
