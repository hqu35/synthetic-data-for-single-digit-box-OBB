#!/usr/bin/env python3
"""Check physical source-code lines for the repository word limit."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+', type=Path)
    args = parser.parse_args()
    failures = 0
    for path in args.files:
        for number, line in enumerate(
            path.read_text().splitlines(), 1
        ):
            words = len(line.split())
            if words > 12:
                print(
                    f'{path}:{number}: {words} words (maximum 12)'
                )
                failures += 1
    return int(failures > 0)


if __name__ == '__main__':
    raise SystemExit(main())
