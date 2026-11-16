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
from geometry_worker.worker import DEFAULT_CONFIG, sample, reconstruct
from geometry_worker.render import make_images, save_sample


class StatisticalGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(DEFAULT_CONFIG.read_text())
        cls.samples = [
            sample(20261104 + i, "43882", cls.config) for i in range(5)
        ]

    def test_geometry_has_five_separated_simple_regions(self):
        for data in self.samples:
            self.assertEqual(len(data["strips"]), 5)
            self.assertTrue(
                all(g > 0 for g in data["minimum_separation_gaps_px"])
            )
            centers = [
                np.asarray(s["coefficients_px"]["p"])
                @ data["separation_axis_px"]
                for s in data["strips"]
            ]
            self.assertEqual(centers, sorted(centers))
            for strip in data["strips"]:
                contour = np.asarray(strip["contour_px"])
                box = np.asarray(strip["obb_px"])
                self.assertTrue(simple_polygon(contour))
                self.assertTrue(points_in_box(contour, box))
                self.assertTrue(
                    points_in_box(
                        boundary(strip["coefficients_px"], 2048),
                        box,
                        tolerance=1e-6,
                    )
                )
                d = strip["jacobian_endpoint_determinants"]
                self.assertGreater(d[0] * d[1], 0)
                edge = box[1] - box[0]
                other = box[2] - box[1]
                self.assertAlmostEqual(float(edge @ other), 0, delta=1e-6)
                self.assertTrue(
                    np.all(
                        (np.asarray(strip["obb_normalized"]) >= 0)
                        & (np.asarray(strip["obb_normalized"]) <= 1)
                    )
                )

    def test_determinism_and_digit_metadata_not_pixels(self):
        a = sample(20261104, "43882", self.config)
        b = sample(20261104, "43882", self.config)
        self.assertEqual(a, b)
        c = sample(20261104, "01234", self.config)
        self.assertEqual(
            make_images(a)[0].tobytes(), make_images(c)[0].tobytes()
        )
        self.assertNotEqual(
            make_images(a)[0].tobytes(),
            make_images(self.samples[1])[0].tobytes(),
        )
        with self.assertRaises(ValueError):
            sample(1, "12x45", self.config)

    def test_saved_labels_and_json_reconstruction(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "a"
            save_sample(self.samples[0], out)
            saved = json.loads((out / "geometry.json").read_text())
            rebuilt = reconstruct(saved)
            self.assertEqual(saved, rebuilt)
            restored = Path(tmp) / "b"
            save_sample(rebuilt, restored)
            for name in (
                "conditioning.png",
                "preview.png",
                "annotations.txt",
                "geometry.json",
            ):
                self.assertEqual(
                    (out / name).read_bytes(),
                    (restored / name).read_bytes(),
                    name,
                )
            rows = (out / "annotations.txt").read_text().splitlines()
            self.assertEqual(len(rows), 5)
            for line, strip in zip(rows, saved["strips"]):
                parts = line.split()
                self.assertEqual(parts[0], "0")
                self.assertEqual(len(parts), 9)
                coords = np.asarray([float(x) for x in parts[1:]]).reshape(
                    4, 2
                )
                self.assertTrue(
                    np.allclose(coords, strip["obb_normalized"], atol=5.1e-11)
                )
                self.assertTrue(
                    np.allclose(
                        coords * saved["resolution"],
                        strip["obb_px"],
                        atol=1e-7,
                    )
                )

    def test_conditioning_has_five_connected_strips(self):
        for data in self.samples:
            image, _ = make_images(data)
            arr = np.asarray(image.convert("L"))
            threshold = (
                data["background_gray"]
                + min(s["fill_gray"] for s in data["strips"])
            ) // 2
            binary = Image.fromarray(
                np.where(arr > threshold, 255, 0).astype("uint8")
            ).copy()
            for strip in data["strips"]:
                x, y = map(round, strip["coefficients_px"]["p"])
                self.assertEqual(binary.getpixel((x, y)), 255)
                ImageDraw.floodfill(binary, (x, y), 128)
            self.assertFalse(
                np.any(np.asarray(binary) == 255),
                "Unexpected disconnected foreground",
            )

    def test_intersection_detection(self):
        self.assertTrue(simple_polygon([[0, 0], [3, 0], [3, 2], [0, 2]]))
        self.assertFalse(simple_polygon([[0, 0], [3, 2], [0, 2], [3, 0]]))
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
        data = sample(19, "01234", config)
        image, _ = make_images(data)
        self.assertEqual(image.size, (640, 640))
        self.assertEqual([s["digit"] for s in data["strips"]], list("01234"))
        self.assertTrue(
            all(
                0 <= v <= 1
                for s in data["strips"]
                for p in s["obb_normalized"]
                for v in p
            )
        )


if __name__ == "__main__":
    unittest.main()
