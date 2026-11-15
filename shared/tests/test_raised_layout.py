import copy
import json
import unittest
from pathlib import Path
from digitgen.raised_layout import raised_layout

ROOT=Path(__file__).resolve().parents[1]


class RaisedLayoutTests(unittest.TestCase):
    def setUp(self):self.c=json.loads((ROOT/'configs/stage1_raised_band.json').read_text())
    def test_requested_width_and_slot_semantics(self):
        d=raised_layout(self.c)
        self.assertAlmostEqual(d['band_width'],.82*.625)
        self.assertAlmostEqual(d['band_width']/d['slot_width'],.8)
        self.assertAlmostEqual(d['left_margin']+d['band_width']+d['right_margin'],d['slot_width'])
        self.assertGreater(d['right_margin'],d['left_margin'])
        self.assertAlmostEqual(d['pitch'],d['slot_width']+d['visible_gap'])
        self.assertGreater(d['physical_clearance'],0)
    def test_edge_attachment_and_radial_clearance(self):
        d=raised_layout(self.c)
        self.assertGreater(d['band_radius'],d['base_radius'])
        self.assertGreater(d['pin_root_x'],d['band_right'])
        self.assertLess(d['pin_tip_x'],d['slot_width']/2)
        self.assertGreater(d['pin_radial_position']-d['pin_radius'],d['base_radius'])
    def test_impossible_dimensions_rejected(self):
        for key,value in [('band_radius',1.0),('pin_length',.4),('base_width',.4),('minimum_clearance',1.0)]:
            c=copy.deepcopy(self.c);c[key]=value
            with self.assertRaises(ValueError):raised_layout(c)


if __name__=='__main__':unittest.main()
