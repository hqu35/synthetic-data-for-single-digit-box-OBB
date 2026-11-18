"""Check nested window geometry and its digit-strip labels."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "2D_Mask_for_Diffusion" / "2d_mask_4_diffusion_V2"
sys.path.insert(0, str(V2))
from mask_v2.render import save_sample
from mask_v2.worker import DEFAULT_CONFIG, sample


class NestedMaskTests(unittest.TestCase):
    def test_window_strip_and_gap_geometry(self):
        config = json.loads(DEFAULT_CONFIG.read_text())
        for count in (5, 6):
            config["window_count"] = count
            data = sample(20261116, config)
            self.assertEqual(len(data["windows"]), count)
            self.assertEqual(len(data["strips"]), count)
            gap = data["sampled_gap_to_window_width"]
            self.assertTrue(0.01 <= gap <= 0.02)
            for window, strip in zip(data["windows"], data["strips"]):
                outer = window["coefficients_px"]
                inner = strip["coefficients_px"]
                np.testing.assert_allclose(inner["p"], outer["p"])
                np.testing.assert_allclose(inner["a"], 0.7*np.array(outer["a"]))
                np.testing.assert_allclose(inner["b"], outer["b"])
                np.testing.assert_allclose(inner["k"], outer["k"])
            windows = data["windows"]
            for left, right in zip(windows, windows[1:]):
                left_c = left["coefficients_px"]
                right_c = right["coefficients_px"]
                a = np.asarray(left_c["a"])
                b = np.asarray(right_c["a"])
                distance = np.asarray(right_c["p"]) - left_c["p"]
                np.testing.assert_allclose(distance, (a+b)*(1+gap))

    def test_mask_colors_and_yolo_labels(self):
        config = json.loads(DEFAULT_CONFIG.read_text())
        data = sample(20261116, config)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "sample"
            save_sample(data, output)
            image = Image.open(output / "conditioning.png").convert("L")
            self.assertEqual(image.getpixel((0, 0)), 0)
            for window, strip in zip(data["windows"], data["strips"]):
                center = np.asarray(strip["coefficients_px"]["p"])
                axis = np.asarray(window["coefficients_px"]["a"])
                inside = tuple(np.rint(center).astype(int))
                margin = tuple(np.rint(center + 0.85*axis).astype(int))
                self.assertEqual(image.getpixel(inside), 155)
                self.assertEqual(image.getpixel(margin), 255)
            rows = (output / "annotations.txt").read_text().splitlines()
            self.assertEqual(len(rows), len(data["strips"]))
            for row, strip in zip(rows, data["strips"]):
                values = row.split()
                self.assertEqual(values[0], "0")
                coords = np.asarray(values[1:], dtype=float).reshape(4, 2)
                np.testing.assert_allclose(coords, strip["obb_normalized"])
            boxes = json.loads((output / "flux_bboxes.json").read_text())
            self.assertEqual(boxes["boxes"], [s["flux_bbox"] for s in data["strips"]])


if __name__ == "__main__":
    unittest.main()
