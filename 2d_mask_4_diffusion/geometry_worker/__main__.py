"""CLI: generate a deterministic batch or reconstruct one saved geometry."""

import argparse, json, sys
from pathlib import Path
from .worker import DEFAULT_CONFIG, sample, upgrade_to_aabb
from .render import save_sample, make_contact_sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(
        dest='command', required=True
    )
    gen = sub.add_parser('generate')
    gen.add_argument('--output', type=Path, required=True)
    gen.add_argument('--count', type=int, default=20)
    gen.add_argument('--seed', type=int, default=20261104)
    gen.add_argument(
        '--config', type=Path, default=DEFAULT_CONFIG
    )
    rec = sub.add_parser('reconstruct')
    rec.add_argument('--input', type=Path, required=True)
    rec.add_argument('--output', type=Path, required=True)
    a = parser.parse_args()
    if a.output.exists():
        parser.error('Output path already exists')
    if a.command == 'reconstruct':
        data = upgrade_to_aabb(
            json.loads(a.input.read_text())
        )
        save_sample(data, a.output)
        print('RECONSTRUCTED', a.output)
        return
    if not 1 <= a.count <= 10000:
        parser.error('count must be between 1 and 10000')
    config = json.loads(a.config.read_text())
    a.output.mkdir(parents=True)
    samples = []
    for i in range(a.count):
        path = a.output / f'sample_{i+1:04d}'
        data = sample(a.seed + i, config)
        save_sample(data, path)
        samples.append(path)
        print(
            'GENERATED',
            path.name,
            'seed',
            a.seed + i,
            flush=True,
        )
    make_contact_sheet(
        samples, a.output / 'contact_sheet.png'
    )
    make_contact_sheet(
        samples,
        a.output / 'conditioning_contact_sheet.png',
        'conditioning.png',
    )
    (a.output / 'batch.json').write_text(
        json.dumps(
            {
                'count': a.count,
                'base_seed': a.seed,
                'samples': [p.name for p in samples],
            },
            indent=2,
        )
        + '\n'
    )
    print('COMPLETE', a.count, flush=True)


if __name__ == '__main__':
    main()
