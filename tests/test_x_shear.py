"""Regression tests for X-only shearing, sampling and projected annotations."""
import math,unittest
from collections import Counter
import numpy as np
from digitgen.shear import make_shear_plan,affine_for_shape,affine_for_scene,map_points,shear_image,transform_regions,transform_framing
from digitgen.geometry import area

class ShearTests(unittest.TestCase):
    def test_adaptive_canvas_protects_register(self):
        for left,right in ((20,100),(0,120)):
            poly=[[left,5],[right,5],[right,75],[left,75]]
            region={'visible_boundary_px':poly,'physical_slot_obb_px':poly}
            affine=affine_for_scene(120,80,.12,{'register_footprint_polygon_px':poly},[region])
            self.assertEqual(affine['horizontal_padding_px']==0,left==20)
            for x,y in map_points(poly,affine):
                self.assertGreaterEqual(x,0);self.assertLessEqual(x,affine['output_resolution'][0])
            self.assertEqual(affine['output_resolution'][1],80)

    def test_stratified_sampling_and_ranges(self):
        seeds=list(range(1000,1020));plan=make_shear_plan(seeds)
        self.assertEqual(plan,make_shear_plan(seeds));self.assertEqual(Counter(x['bucket'] for x in plan),{'subtle':10,'natural':6,'strong':4})
        bounds={'subtle':.03,'natural':.08,'strong':.12}
        self.assertTrue(all(-bounds[x['bucket']]<=x['s']<=bounds[x['bucket']] for x in plan))
        self.assertEqual([x['s'] for x in make_shear_plan(seeds,False)],[0.]*20)
        self.assertNotEqual(plan,make_shear_plan(list(range(2000,2020))))

    def test_x_only_and_padding(self):
        for s in (-.12,-.03,0,.03,.12):
            a=affine_for_shape(120,80,s);pts=[[0,0],[120,0],[120,80],[0,80],[31,17]];out=map_points(pts,a)
            for (x,y),(xx,yy) in zip(pts,out):
                self.assertAlmostEqual(xx,x+s*(y-40)+a['horizontal_padding_px']);self.assertEqual(y,yy)
                self.assertTrue(0<=xx<=a['output_resolution'][0])
            self.assertEqual(a['output_resolution'][1],80)
        for bad in [-.121,.121,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):affine_for_shape(120,80,bad)

    def test_raster_moves_horizontally_without_changing_rows(self):
        image=np.zeros((30,80,3),dtype=np.uint8);image[7:23,30:33]=255
        a=affine_for_shape(80,30,.1);out=shear_image(image,a)
        self.assertEqual(out.shape,(30,a['output_resolution'][0],3));self.assertFalse(out[:7].any());self.assertFalse(out[23:].any())
        for y in (7,15,22):
            xs=np.arange(out.shape[1]);row=out[y,:,0].astype(float);centroid=(xs@row)/row.sum()
            self.assertAlmostEqual(centroid,31+.1*(y-15)+a['horizontal_padding_px'],delta=.05)
        self.assertTrue(np.array_equal(shear_image(image,affine_for_shape(80,30,0)),image))

    def test_transformed_contour_is_enclosed_by_refitted_rectangle(self):
        poly=[[20,10],[40,11],[41,40],[18,39]]
        reg={'visible_boundary_px':poly,'obb_px':[[18,10],[41,10],[41,40],[18,40]],'physical_slot_obb_px':[[16,8],[44,8],[44,42],[16,42]],'checks':{},'angle_deg':0,'projected_obb_width_to_slot_ratio':.8}
        for s in (-.12,.12):
            a=affine_for_shape(80,50,s);r=transform_regions([reg],a)[0];self.assertEqual(r['visible_boundary_px'],map_points(poly,a));self.assertGreater(area(r['obb_px']),0)
            edges=[(b[0]-x[0],b[1]-x[1]) for x,b in zip(r['obb_px'],r['obb_px'][1:]+r['obb_px'][:1])]
            self.assertAlmostEqual(edges[0][0]*edges[1][0]+edges[0][1]*edges[1][1],0,delta=1e-6)
            for x,y in r['visible_boundary_px']:
                for p,q in zip(r['obb_px'],r['obb_px'][1:]+r['obb_px'][:1]):self.assertGreaterEqual((q[0]-p[0])*(y-p[1])-(q[1]-p[1])*(x-p[0]),-1e-5)
            self.assertEqual(r['pre_shear_projection']['visible_boundary_px'],poly)
            f=transform_framing({'register_area_fraction':.9,'register_footprint_polygon_px':poly},a)
            self.assertAlmostEqual(f['register_area_fraction'],.9*80/a['output_resolution'][0])

if __name__=='__main__':unittest.main()
