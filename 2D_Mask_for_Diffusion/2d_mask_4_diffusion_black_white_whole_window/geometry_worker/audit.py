"""Check the image dimensions and annotation formats of a saved batch."""

import argparse
import json
import math
from pathlib import Path
from PIL import Image


def audit(root):
    root = Path(root)
    batch = json.loads((root / "batch.json").read_text())
    records = []
    for name in batch["samples"]:
        folder = root / name
        data = json.loads((folder / "geometry.json").read_text())
        strips = data["strips"]
        with Image.open(folder / "conditioning.png") as image:
            if list(image.size) != data["resolution"]:
                raise ValueError(f"{name}: image size differs from geometry")
        rows = (folder / "annotations.txt").read_text().splitlines()
        if len(rows) != len(strips):
            raise ValueError(f"{name}: strip and annotation counts differ")
        for line in rows:
            fields = line.split()
            expected = 5 if data.get("schema_version", 1) == 2 else 9
            if len(fields) != expected or fields[0] != "0":
                raise ValueError(f"{name}: incorrect annotation format")
            if any(
                not math.isfinite(x) or not 0 <= x <= 1
                for x in map(float, fields[1:])
            ):
                raise ValueError(f"{name}: annotation outside 0–1")
        if data.get("schema_version", 1) >= 3:
            flux = json.loads((folder / "flux_bboxes.json").read_text())
            if len(flux["boxes"]) != len(strips):
                raise ValueError(f"{name}: strip and FLUX box counts differ")
            for top, left, bottom, right in flux["boxes"]:
                if not (
                    0 <= top < bottom <= 1000 and 0 <= left < right <= 1000
                ):
                    raise ValueError(f"{name}: invalid FLUX box")
        records.append({"sample": name, "strips": len(strips)})
        print("AUDIT_OK", name, flush=True)
    return {
        "status": "passed",
        "sample_count": len(records),
        "samples": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = audit(args.directory)
    (args.directory / "validation.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print("AUDIT_COMPLETE", result["sample_count"])


if __name__ == "__main__":
    main()
