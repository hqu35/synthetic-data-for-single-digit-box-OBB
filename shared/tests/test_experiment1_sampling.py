import copy
import json
from pathlib import Path
import unittest
from digitgen.experiment1_sampling import sample_parameters


class Experiment1Tests(unittest.TestCase):
    def setUp(self):
        self.c=json.loads((Path(__file__).resolve().parents[1]/'configs/diffusion_exp1.json').read_text())

    def test_replay_independent_of_generation_order(self):
        ordered={i:sample_parameters(self.c,i) for i in range(1,101)}
        self.assertEqual(ordered,{i:sample_parameters(self.c,i) for i in range(100,0,-1)})
        self.assertEqual(len({p['seed'] for p in ordered.values()}),100)
        self.assertEqual(sum(p['lighting']['preset']=='neutral' for p in ordered.values()),50)
        self.assertEqual(sum(p['lighting']['preset']=='cool_blue' for p in ordered.values()),50)

    def test_retries_are_distinct_bounded_and_configured(self):
        seen=set()
        for i in range(1,101):
            for attempt in range(3):
                p=sample_parameters(self.c,i,attempt);self.assertNotIn(p['seed'],seen);seen.add(p['seed'])
                for key in ['yaw_deg','pitch_deg','roll_deg','distance','focal_length_mm']:
                    self.assertTrue(self.c['camera'][key][0]<=p['camera'][key]<=self.c['camera'][key][1])
        for i,attempt in [(0,0),(101,0),(1,3),(1,-1)]:
            with self.assertRaises(ValueError):sample_parameters(self.c,i,attempt)

    def test_sampling_keeps_identity_and_does_not_modify_config(self):
        prior=copy.deepcopy(self.c)
        for i in range(1,101):sample_parameters(self.c,i)
        self.assertEqual(prior,self.c)
        self.assertEqual(self.c['preserved']['digit_sequence'],'00054')
        self.assertEqual(self.c['preserved']['transition_progress'],[0,0,0,0,.05])

    def test_200_view_framing_and_replay(self):
        c=json.loads((Path(__file__).resolve().parents[1]/'configs/diffusion_exp1_200.json').read_text())
        original=copy.deepcopy(c);samples=[sample_parameters(c,i) for i in range(1,201)]
        self.assertEqual(c,original)
        self.assertEqual(len({p['seed'] for p in samples}),200)
        self.assertEqual(sum(p['lighting']['preset']=='cool_blue' for p in samples),100)
        self.assertEqual(samples[-1],sample_parameters(c,200))
        for p in samples:
            self.assertTrue(.90<=p['camera']['target_register_area_fraction']<=.95)
            self.assertLessEqual(abs(p['camera']['roll_deg']),.25)
        with self.assertRaises(ValueError):sample_parameters(c,201)

    def test_five_review_poses_are_deterministic_and_cover_both_sides(self):
        c=json.loads((Path(__file__).resolve().parents[1]/'configs/perspective_review.json').read_text())
        poses=[sample_parameters(c,i)['camera'] for i in range(1,6)]
        self.assertEqual([p['yaw_deg'] for p in poses],[-14,-14,14,14,15])
        self.assertEqual(len({(p['yaw_deg'],p['pitch_deg'],p['distance']) for p in poses}),5)
        self.assertTrue(all(p['target_register_area_fraction']==.905 for p in poses))
        self.assertEqual(poses[3],sample_parameters(c,4)['camera'])
        with self.assertRaises(ValueError):sample_parameters(c,6)


if __name__=='__main__':unittest.main()
