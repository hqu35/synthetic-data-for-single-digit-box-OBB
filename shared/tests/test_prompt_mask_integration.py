"""Check the geometry-to-prompt handoff and independent prompt sampling."""

import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "Flux3_kelin_ComfyUI_workflow" / "Prompt_generator"
sys.path.insert(0, str(SCRIPTS))
from watermeter_geometry import load_layout
from watermeter_prompt_generator import generate_configuration, make_prompt


class PromptMaskIntegrationTests(unittest.TestCase):
    def generate(self, root, prompt_seed="7"):
        dest = root / ("sample_" + prompt_seed)
        subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "watermeter_generate_layout_prompt.py"),
                "--output",
                str(dest),
                "--mask-seed",
                "42",
                "--prompt-seed",
                prompt_seed,
                "--scenario",
                "one_rolling",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return dest

    def test_mask_positions_and_independent_digit_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = self.generate(root, "7")
            b = self.generate(root, "8")
            la = load_layout(a / "mask")
            lb = load_layout(b / "mask")
            self.assertEqual(la["windows"], lb["windows"])
            self.assertEqual(la["digit_count"], 5)
            ra = json.loads((a / "layout_prompt.json").read_text())
            rb = json.loads((b / "layout_prompt.json").read_text())
            self.assertNotEqual(
                ra["prompt_config"]["windows"], rb["prompt_config"]["windows"]
            )
            self.assertEqual(
                ra["prompt_config"]["digit_count"], la["digit_count"]
            )
            geometry = json.loads((a / "mask/geometry.json").read_text())
            self.assertNotIn("reading", geometry)
            self.assertTrue(
                all("digit" not in strip for strip in geometry["strips"])
            )
            self.assertEqual(
                ra["layout"]["mask_image"], "mask/conditioning.png"
            )
            self.assertEqual(ra["layout"]["windows"], la["windows"])
            for w in la["windows"]:
                self.assertIn(
                    '"bbox":'
                    + json.dumps(
                        w["flux_aabb_yxyx_1000"], separators=(",", ":")
                    ),
                    ra["prompt"],
                )
            self.assertEqual(len(ra["yolo_obb_label_lines"]), 5)
            self.assertTrue(
                all(
                    len(row.split()) == 9 for row in ra["yolo_obb_label_lines"]
                )
            )

    def test_layout_loader_reads_geometry_without_auxiliary_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self.generate(Path(tmp))
            (p / "mask/flux_bboxes.json").unlink()
            (p / "mask/annotations.txt").unlink()
            geometry = p / "mask/geometry.json"
            d = json.loads(geometry.read_text())
            d["reading"] = "99999"
            for s in d["strips"]:
                s["digit"] = "9"
            geometry.write_text(json.dumps(d))
            layout = load_layout(p / "mask")
            self.assertEqual(layout["digit_count"], 5)
            self.assertNotIn("reading", layout)
            self.assertEqual(
                layout["windows"][0]["flux_aabb_yxyx_1000"],
                d["strips"][0]["flux_bbox"],
            )

    def test_manifest_uses_mask_count_and_independent_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = self.generate(root)
            for folder in ("clear", "noisy"):
                (root / folder).mkdir()
                for i in range(9):
                    Image.new("RGB", (8, 8), (i, 20, 30)).save(
                        root / folder / f"{folder}_{i}.png"
                    )
            out = root / "manifest.jsonl"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "watermeter_build_manifest.py"),
                    "--clear-dir",
                    str(root / "clear"),
                    "--noisy-dir",
                    str(root / "noisy"),
                    "--layouts-dir",
                    str(sample / "mask"),
                    "--out",
                    str(out),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            rows = [json.loads(line) for line in out.read_text().splitlines()]
            self.assertEqual(len(rows), 100)
            for row in rows:
                self.assertNotIn("reading", row["layout_geometry"])
                self.assertEqual(
                    len(row["prompt_config"]["windows"]),
                    row["layout_geometry"]["digit_count"],
                )
                self.assertEqual(
                    row["reference_images_ordered"][-1],
                    str((sample / "mask/conditioning.png").resolve()),
                )
                self.assertEqual(len(row["yolo_obb_label_lines"]), 5)

    def test_prompt_requires_same_number_of_boxes_and_windows(self):
        cfg = generate_configuration(5, 1)
        with self.assertRaises(ValueError):
            make_prompt(cfg, [[0, 0, 100, 100]])


if __name__ == "__main__":
    unittest.main()
