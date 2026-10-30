"""Host-Python entry point: render with Blender, then audit saved files."""
import argparse
import shutil
import subprocess
from pathlib import Path
from digitgen.config import load_config
from validate import audit
from prepare_assets import prepare

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender',default=shutil.which('blender') or '/Applications/Blender.app/Contents/MacOS/Blender')
    parser.add_argument('--config',default='configs/preview.json')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--count',type=int)
    parser.add_argument('--index',type=int)
    parser.add_argument('--rolling-preview',action='store_true')
    args = parser.parse_args()
    config = load_config(ROOT/args.config)
    prepare(config)
    output = (args.output or ROOT/config['output']).resolve()
    command = [args.blender,'--background','--factory-startup','--python-exit-code','1',
               '--python',str(ROOT/'generate.py'),'--','--config',str(ROOT/args.config),'--output',str(output)]
    for key in ('count','index'):
        value = getattr(args,key)
        if value is not None:
            command.extend(['--'+key,str(value)])
    if args.rolling_preview:
        command.append('--rolling-preview')
    subprocess.run(command,check=True,cwd=ROOT)
    audit(output)


if __name__=='__main__':
    main()
