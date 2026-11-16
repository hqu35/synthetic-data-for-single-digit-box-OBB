import copy, json, math, tempfile, unittest
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from geometry_worker.geometry import (
    boundary,
    min_area_rect,
    points_in_box,
    simple_polygon,
)
from geometry_worker.worker import (
    DEFAULT_CONFIG,
    sample,
    reconstruct,
    upgrade_to_aabb,
    flux_bbox_from_strip,
)
from geometry_worker.render import make_images, save_sample
from geometry_worker.audit import audit


class StatisticalGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(DEFAULT_CONFIG.read_text())
        cls.samples = [
            sample(20261104 + i, cls.config)
            for i in range(5)
        ]

    def test_geometry_has_five_separated_simple_regions(
        self,
    ):
        for data in self.samples:
            self.assertEqual(len(data['strips']), 5)
            self.assertTrue(
                all(
                    g > 0
                    for g in data[
                        'minimum_separation_gaps_px'
                    ]
                )
            )
            centers = [
                np.asarray(s['coefficients_px']['p'])
                @ data['separation_axis_px']
                for s in data['strips']
            ]
            self.assertEqual(centers, sorted(centers))
            for strip in data['strips']:
                contour = np.asarray(strip['contour_px'])
                box = np.asarray(strip['obb_px'])
                self.assertTrue(simple_polygon(contour))
                self.assertTrue(points_in_box(contour, box))
                self.assertTrue(
                    points_in_box(
                        boundary(
                            strip['coefficients_px'], 2048
                        ),
                        box,
                        tolerance=1e-6,
                    )
                )
                d = strip['jacobian_endpoint_determinants']
                self.assertGreater(d[0] * d[1], 0)
                edge = box[1] - box[0]
                other = box[2] - box[1]
                self.assertAlmostEqual(
                    float(edge @ other), 0, delta=1e-6
                )
                self.assertTrue(
                    np.all(
                        (
                            np.asarray(
                                strip['obb_normalized']
                            )
                            >= 0
                        )
                        & (
                            np.asarray(
                                strip['obb_normalized']
                            )
                            <= 1
                        )
                    )
                )

    def test_determinism_and_digit_metadata_not_pixels(
        self,
    ):
        a = sample(20261104, self.config)
        b = sample(20261104, self.config)
        self.assertEqual(a, b)
        self.assertNotIn('reading', a)
        self.assertTrue(
            all(
                'digit' not in strip
                for strip in a['strips']
            )
        )
        self.assertNotEqual(
            make_images(a)[0].tobytes(),
            make_images(self.samples[1])[0].tobytes(),
        )

    def test_saved_labels_and_json_reconstruction(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'a'
            save_sample(self.samples[0], out)
            saved = json.loads(
                (out / 'geometry.json').read_text()
            )
            rebuilt = reconstruct(saved)
            self.assertEqual(saved, rebuilt)
            restored = Path(tmp) / 'b'
            save_sample(rebuilt, restored)
            for name in (
                'conditioning.png',
                'preview.png',
                'annotations.txt',
                'geometry.json',
                'flux_bboxes.json',
            ):
                self.assertEqual(
                    (out / name).read_bytes(),
                    (restored / name).read_bytes(),
                    name,
                )
            rows = (
                (out / 'annotations.txt')
                .read_text()
                .splitlines()
            )
            self.assertEqual(len(rows), 5)
            for line, strip in zip(rows, saved['strips']):
                parts = line.split()
                self.assertEqual(parts[0], '0')
                self.assertEqual(len(parts), 9)
                coords = np.asarray(
                    [float(x) for x in parts[1:]]
                ).reshape(4, 2)
                self.assertTrue(
                    np.allclose(
                        coords,
                        strip['obb_normalized'],
                        atol=5.1e-11,
                    )
                )
                self.assertTrue(
                    np.allclose(
                        coords
                        * np.array(saved['resolution']),
                        strip['obb_px'],
                        atol=1e-7,
                    )
                )
                contour = np.asarray(strip['contour_px'])
                expected = np.r_[
                    contour.min(axis=0), contour.max(axis=0)
                ]
                self.assertTrue(
                    np.allclose(
                        strip['aabb_px'],
                        expected,
                        atol=1e-10,
                    )
                )
                self.assertEqual(
                    strip['flux_bbox'],
                    flux_bbox_from_strip(
                        strip['coefficients_px'],
                        *saved['resolution']
                    ),
                )
            self.assertEqual(
                json.loads(
                    (out / 'flux_bboxes.json').read_text()
                )['boxes'],
                [s['flux_bbox'] for s in saved['strips']],
            )

    def test_conditioning_has_five_connected_strips(self):
        for data in self.samples:
            image, _ = make_images(data)
            arr = np.asarray(image.convert('L'))
            threshold = (
                data['background_gray']
                + min(
                    s['fill_gray'] for s in data['strips']
                )
            ) // 2
            binary = Image.fromarray(
                np.where(arr > threshold, 255, 0).astype(
                    'uint8'
                )
            ).copy()
            for strip in data['strips']:
                x, y = map(
                    round, strip['coefficients_px']['p']
                )
                self.assertEqual(
                    binary.getpixel((x, y)), 255
                )
                ImageDraw.floodfill(binary, (x, y), 128)
            self.assertFalse(
                np.any(np.asarray(binary) == 255),
                'Unexpected disconnected foreground',
            )

    def test_intersection_detection(self):
        self.assertTrue(
            simple_polygon([[0, 0], [3, 0], [3, 2], [0, 2]])
        )
        self.assertFalse(
            simple_polygon([[0, 0], [3, 2], [0, 2], [3, 0]])
        )
        angle = 0.37
        rotation = np.array(
            [
                [math.cos(angle), -math.sin(angle)],
                [math.sin(angle), math.cos(angle)],
            ]
        )
        rectangle = np.array(
            [[0, 0], [173, 0], [173, 27], [0, 27]]
        ) @ rotation.T + [300, 200]
        box, area = min_area_rect(rectangle)
        self.assertAlmostEqual(area, 173 * 27, places=6)
        self.assertTrue(points_in_box(rectangle, box))

    def test_alternative_resolution(self):
        config = copy.deepcopy(self.config)
        config.update(width=640, height=640)
        data = sample(19, config)
        image, _ = make_images(data)
        self.assertEqual(image.size, (640, 640))
        self.assertTrue(
            all(
                'digit' not in strip
                for strip in data['strips']
            )
        )
        self.assertTrue(
            all(
                0 <= v <= 1
                for s in data['strips']
                for p in s['obb_normalized']
                for v in p
            )
        )

    def test_legacy_geometry_can_be_upgraded_without_moving_contours(
        self,
    ):
        old = copy.deepcopy(self.samples[0])
        old['schema_version'] = 1
        for strip in old['strips']:
            strip.pop('aabb_px')
            strip.pop('aabb_normalized')
            strip.pop('flux_bbox')
        new = upgrade_to_aabb(old)
        self.assertEqual(new['schema_version'], 6)
        for a, b in zip(old['strips'], new['strips']):
            self.assertEqual(
                a['contour_px'], b['contour_px']
            )
            self.assertEqual(a['obb_px'], b['obb_px'])
            self.assertEqual(len(b['aabb_normalized']), 4)
            self.assertEqual(len(b['flux_bbox']), 4)

    def test_flux_order_scale_and_obb_preservation(self):
        coeff = {
            'p': [50, 50],
            'a': [20, 1],
            'b': [5, 35],
            'k': [10, 0],
        }
        box = flux_bbox_from_strip(coeff, 100, 100)
        dense = boundary(coeff, 10000)
        top, left, bottom, right = box
        self.assertTrue(np.all(dense[:, 0] >= left / 10))
        self.assertTrue(np.all(dense[:, 0] <= right / 10))
        self.assertTrue(np.all(dense[:, 1] >= top / 10))
        self.assertTrue(np.all(dense[:, 1] <= bottom / 10))
        self.assertLess(
            left, 350
        )  # the curved side extends left of the top-left corner
        with self.assertRaises(ValueError):
            flux_bbox_from_strip(
                {
                    'p': [0, 0],
                    'a': [10, 0],
                    'b': [0, 10],
                    'k': [0, 0],
                },
                100,
                100,
            )

    def test_batch_format_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_sample(
                self.samples[0], root / 'sample_0001'
            )
            (root / 'batch.json').write_text(
                json.dumps(
                    {'count': 1, 'samples': ['sample_0001']}
                )
            )
            self.assertEqual(audit(root)['sample_count'], 1)
            Image.new('RGB', (64, 64)).save(
                root / 'sample_0001' / 'conditioning.png'
            )
            with self.assertRaisesRegex(
                ValueError, 'image size'
            ):
                audit(root)


if __name__ == '__main__':
    unittest.main()
