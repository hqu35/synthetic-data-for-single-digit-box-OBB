import json, math, tempfile, unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
from PIL import Image
from digitgen.assets import texture_spec, verify_spec
from digitgen.sampling import wheel_state
from digitgen import photo_atlas

ROOT=Path(__file__).resolve().parents[1]

class RollingAtlasTests(unittest.TestCase):
    def test_increasing_digit_enters_from_bottom(self):
        # Reversed physical tile order and negative rotation make an increasing
        # sequence move upward: current digit above, next digit below.
        pitch=2*math.pi/10
        for digit in range(10):
            rotation=-wheel_state(0,digit,.5)['wheel_rotation']
            current_y=math.sin(-digit*pitch-rotation)
            next_y=math.sin(-(digit+1)*pitch-rotation)
            self.assertGreater(current_y,0)
            self.assertLess(next_y,0)
            self.assertEqual((digit+1)%10,wheel_state(0,digit,.5)['next_digit'])

    def test_photo_source_and_distinct_digits(self):
        config=json.loads((ROOT/'configs/rolling_numerals_atlas.json').read_text())
        atlas=texture_spec(config);verify_spec(atlas)
        self.assertIn('source_image',atlas)
        image=np.asarray(Image.open(ROOT/atlas['path']).convert('L'))
        step=config['typography']['segment_pixels']
        tiles=[image[:,digit*step:(digit+1)*step].tobytes() for digit in range(10)]
        self.assertEqual(len(set(tiles)),10)
        original_config=json.loads(json.dumps(config));original_config['typography'].pop('tile_order')
        original_config['typography']['image_source']=str(ROOT/original_config['typography']['image_source'])
        with tempfile.TemporaryDirectory() as tmp, patch.object(photo_atlas,'ROOT',Path(tmp)):
            reference,_=photo_atlas.build_photo_atlas(original_config)
            original=np.asarray(Image.open(reference).convert('L'))
        for tile_index,digit in enumerate(config['typography']['tile_order']):
            self.assertTrue(np.array_equal(image[:,tile_index*step:(tile_index+1)*step],
                                           original[:,digit*step:(digit+1)*step]))
        four_tile=config['typography']['tile_order'].index(4)
        tile=Image.fromarray(image[:,four_tile*step:(four_tile+1)*step]).transpose(Image.Transpose.TRANSVERSE)
        mask=tile.point(lambda v:255 if v>128 else 0)
        from PIL import ImageDraw
        ImageDraw.floodfill(mask,(step//2,step//2),128,thresh=0)
        self.assertEqual(mask.getpixel((step//2,step//2)),128)
        self.assertEqual(mask.getpixel((0,0)),0)

    def test_ten_centered_separate_glyphs_and_wraparound(self):
        config=json.loads((ROOT/'configs/rolling_numerals_atlas.json').read_text())
        atlas=texture_spec(config);verify_spec(atlas)
        image=np.asarray(Image.open(ROOT/atlas['path']).convert('L'))
        step=config['typography']['segment_pixels'];self.assertEqual(image.shape,(1024,10*step))
        for digit in range(10):
            tile=image[:,digit*step:(digit+1)*step]
            self.assertFalse(tile[:,0].any());self.assertFalse(tile[:,-1].any())
            ys,xs=np.where(tile>128);self.assertGreater(len(xs),0)
            self.assertAlmostEqual((xs.min()+xs.max())/2,(step-1)/2,delta=8)
            self.assertGreater(xs.max()-xs.min(),step*.87)
            self.assertLess(xs.max()-xs.min(),step*.93)
        zero=image[:,:step];ys,xs=np.where(zero>128)
        width_fraction=(ys.max()-ys.min()+1)/image.shape[0]*.7
        angular_height=(xs.max()-xs.min()+1)/step*2*math.pi/10
        g=config['geometry'];radius=g['original_band_radius']*g['wheel_radius_scale']
        height_fraction=2*radius*math.sin(angular_height/2)/(.74*g['window_height_scale'])
        self.assertAlmostEqual(width_fraction,.55,delta=.025)
        self.assertAlmostEqual(height_fraction,.75,delta=.03)
        self.assertAlmostEqual(wheel_state(0,9,0)['wheel_rotation']+2*3.141592653589793/10,
                               wheel_state(0,0,0)['wheel_rotation']+2*3.141592653589793)

if __name__=='__main__':unittest.main()
