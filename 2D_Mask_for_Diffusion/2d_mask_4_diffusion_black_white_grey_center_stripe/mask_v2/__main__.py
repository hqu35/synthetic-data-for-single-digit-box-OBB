"""Generate nested masks and centered-strip annotations."""

import argparse
import json
from pathlib import Path

from .render import save_sample
from .worker import DEFAULT_CONFIG, sample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261116)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--windows", type=int, choices=(5, 6))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output path already exists")
    if args.count < 1:
        parser.error("Count must be positive")
    config = json.loads(DEFAULT_CONFIG.read_text())
    if args.windows is not None:
        config["window_count"] = args.windows
    args.output.mkdir(parents=True)
    for index in range(args.count):
        data = sample(args.seed + index, config)
        output = args.output / f"sample_{index + 1:04d}"
        save_sample(data, output)
        print("GENERATED", output.name, flush=True)


if __name__ == "__main__":
    main()
