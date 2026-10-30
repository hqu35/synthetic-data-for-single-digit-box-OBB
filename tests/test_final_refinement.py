import copy
import json
import unittest
from pathlib import Path
from PIL import Image,ImageFont,ImageDraw
from digitgen.raised_layout import raised_layout
from digitgen.pin_calibration import calibrate_pins
from digitgen.assets import texture_spec

ROOT=Path(__file__).resolve().parents[1]


class FinalRefinementTests(unittest.TestCase):
    def setUp(self):self.c=json.loads((ROOT/'configs/stage1_final_refinement.json').read_text())

    def test_slot_and_pitch_fixed_centered_seventy_percent_band(self):
        previous=json.loads((ROOT/'configs/stage1_raised_band.json').read_text())
        before=raised_layout(previous);d=raised_layout(self.c)
        for key in ('slot_width','pitch','base_radius','band_radius','base_width'):self.assertAlmostEqual(d[key],before[key])
        self.assertAlmostEqual(d['band_center'],0)
        self.assertAlmostEqual(d['left_margin'],.15*d['slot_width'])
        self.assertAlmostEqual(d['right_margin'],d['left_margin'])
        self.assertAlmostEqual(d['band_to_slot_ratio'],.7)
        self.assertGreater(d['physical_clearance'],.09)

    def test_visible_density_is_calibrated_not_count_assumed(self):
        three,four=calibrate_pins(self.c,3),calibrate_pins(self.c,4)
        self.assertEqual(three['total_pin_count'],30);self.assertEqual(three['pin_pitch_degrees'],12)
        self.assertEqual(four['total_pin_count'],40);self.assertEqual(four['pin_pitch_degrees'],9)
        self.assertEqual(four['pin_phase_offset_degrees'],4.5)
        with self.assertRaises(ValueError):calibrate_pins(self.c,5)

    def test_regular_font_is_thinner_not_just_squeezed(self):
        t=self.c['typography'];old=self.c['previous_typography']
        font=ImageFont.truetype(str(ROOT/t['font']),400)
        heavy=ImageFont.truetype(str(ROOT/old['font']),400)
        self.assertEqual(font.getname()[1],'Regular')
        def ink_coverage(f):
            b=f.getbbox('0');im=Image.new('L',(b[2]-b[0],b[3]-b[1]))
            ImageDraw.Draw(im).text((-b[0],-b[1]),'0',font=f,fill=255)
            return sum(v>127 for v in im.getdata())/(im.width*im.height)
        self.assertLess(ink_coverage(font),ink_coverage(heavy))
        spec=texture_spec(self.c)
        with Image.open(ROOT/spec['path']) as atlas:
            self.assertFalse(atlas.crop((0,0,1,atlas.height)).getbbox())
            self.assertFalse(atlas.crop((atlas.width-1,0,atlas.width,atlas.height)).getbbox())
            tile=atlas.crop((0,0,t['segment_pixels'],t['axial_pixels'])).transpose(Image.Transpose.TRANSVERSE)
            bounds=tile.getbbox();actual_height=bounds[3]-bounds[1]
            expected=t['segment_pixels']*t['numeral_height']*t['glyph_height_scale']
            self.assertLess(abs(actual_height-expected),8)


if __name__=='__main__':unittest.main()
