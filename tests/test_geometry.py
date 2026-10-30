import copy
import math
from pathlib import Path
import random
import tempfile
import unittest

from digitgen.config import load_config, validate_config
from digitgen.export import export_labels, read_labels
from digitgen.geometry import area, minimum_rectangle, validate_boxes, convex_intersection
from digitgen.sampling import sample_parameters, wheel_state

ROOT = Path(__file__).resolve().parents[1]


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.c = load_config(ROOT/'configs/preview.json')

    def test_rotated_rectangles_and_corner_order(self):
        for angle in [-20,-12,-2,2,12,20]:
            theta = math.radians(angle)
            points = [[x*math.cos(theta)-y*math.sin(theta)+320,
                       x*math.sin(theta)+y*math.cos(theta)+160] for x,y in [(-25,-50),(25,-50),(25,50),(-25,50)]]
            box, measured = minimum_rectangle(points)
            self.assertAlmostEqual(measured,angle,places=9)
            self.assertAlmostEqual(area(box),5000,places=7)
            self.assertGreater(area(box),0)
            validate_boxes([box],[points],[640,320],angle,self.c['rotation'])

    def test_encloses_general_perspective_quad(self):
        points = [[0,0],[10,1],[9,20],[1,18]]
        box, _ = minimum_rectangle(points)
        self.assertGreaterEqual(area(box),abs(area(points)))
        for x,y in points:
            for a,b in zip(box,box[1:]+box[:1]):
                self.assertGreaterEqual((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]),-1e-8)

    def test_hull_handles_unordered_curved_boundary(self):
        points = [[math.cos(i/10)*20, math.sin(i/10)*30] for i in range(63)]
        random.Random(12).shuffle(points)
        box,_ = minimum_rectangle(points+points[:2])
        self.assertGreater(area(box),1800)

    def test_degenerate_rejected(self):
        for points in [[],[[0,0]],[[0,0],[1,1],[2,2]]]:
            with self.assertRaises(ValueError):
                minimum_rectangle(points)

    def test_label_roundtrip_uses_pixel_metric(self):
        points = [[200,100],[250,120],[230,170],[180,150]]
        box,_ = minimum_rectangle(points)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'label.txt'
            export_labels(path,[box],[640,320])
            loaded = read_labels(path,[640,320])[0]
        for a,b in zip(box,loaded):
            for x,y in zip(a,b):
                self.assertAlmostEqual(x,y,places=6)

    def test_sampling_reproducible_balanced_and_nonoverlapping(self):
        samples = [sample_parameters(self.c,i) for i in range(50)]
        self.assertEqual(samples,[sample_parameters(self.c,i) for i in range(50)])
        self.assertEqual(sum(p['requested_angle_deg']>0 for p in samples),25)
        self.assertEqual({p['digit_count'] for p in samples},{5,6})
        for p in samples:
            self.assertTrue(2<=abs(p['requested_angle_deg'])<=20)
            self.assertAlmostEqual(p['pitch'],p['slot_width']*(1+p['gap_ratio']))
            self.assertLess(p['wheel_width'],p['pitch'])
        self.assertTrue(any(w['transition'] for p in samples for w in p['wheels']))
        self.assertTrue(any(not w['transition'] for p in samples for w in p['wheels']))

    def test_rotation_direction_continuity_and_wrap(self):
        r = 2
        step = 2*math.pi/10
        for digit in range(10):
            for t in (0,.25,.5,.75,.999999):
                state = wheel_state(0,digit,t)
                # Numeral d is initially at angular location d*step. +X axle
                # rotation subtracts state angle from its cylindrical y angle.
                y_current = r*math.sin(digit*step-state['wheel_rotation'])
                y_next = r*math.sin(((digit+1)%10)*step-state['wheel_rotation'])
                self.assertLessEqual(y_current,1e-12)
                self.assertGreater(y_next,-1e-12)
            near_end = wheel_state(0,digit,1-1e-9)['wheel_rotation']
            successor = wheel_state(0,(digit+1)%10,0)['wheel_rotation']
            self.assertAlmostEqual(math.cos(near_end),math.cos(successor),places=8)
            self.assertAlmostEqual(math.sin(near_end),math.sin(successor),places=8)

    def test_config_rejects_invalid_geometry_and_distribution(self):
        for path,value in [(('rotation','min_deg'),0), (('geometry','gap_ratio'),[-.2,.1]),
                           (('geometry','frame_depth'),0), (('digit_counts',),{'7':1}),
                           (('wheels','transition_progress_max'),1),(('annotation_target',),'tight_glyph')]:
            c = copy.deepcopy(self.c)
            node = c
            for key in path[:-1]:
                node=node[key]
            node[path[-1]]=value
            with self.assertRaises(ValueError):
                validate_config(c)

    def test_solid_aperture_intersection(self):
        front=[[0,0],[10,0],[10,10],[0,10]]
        back=[[1,1],[11,1],[11,11],[1,11]]
        self.assertAlmostEqual(area(convex_intersection(front,back)),81)

    def test_clearance_includes_rims_and_pins(self):
        for i in range(100):
            p=sample_parameters(self.c,i);m=p['mechanics']
            self.assertAlmostEqual(m['assembly_width'],p['wheel_width']+m['rim_width']+m['pin_length'])
            self.assertAlmostEqual(p['pitch']-m['assembly_width'],m['wheel_axial_clearance'])
            self.assertIn(m['pin_count'],(20,30))
            self.assertLess(m['pin_radial_position']+m['pin_radius'],m['rim_radius'])

    def test_independent_randomization_groups(self):
        c=copy.deepcopy(self.c);c['randomization']['geometry']=False
        a,b=sample_parameters(c,0),sample_parameters(c,1)
        for key in ('wheel_width','pitch','gap_ratio','digit_count','mechanics'):
            self.assertEqual(a[key],b[key])
        self.assertNotEqual(a['photograph'],b['photograph'])
        c['camera_appearance']['preset']='cool_blue'
        b=sample_parameters(c,1)
        self.assertEqual(a['appearance'],sample_parameters(c,0)['appearance'])
        self.assertGreater(b['photograph']['postprocess_color_cast'][2],b['photograph']['postprocess_color_cast'][0])
        c['randomization']['camera_pose']=False
        c['rotation']['max_deg']=5
        self.assertEqual(sample_parameters(c,0)['requested_angle_deg'],3.5)


if __name__=='__main__':
    unittest.main()
