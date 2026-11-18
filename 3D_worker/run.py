"""Host-Python entry point: render with Blender, then audit saved files."""

# Load the single shared package without worker-local asset links.
import sys as _shared_sys
from pathlib import Path as _SharedPath

_shared_sys.path.insert(
    0,
    str(
        next(
            p / "shared"
            for p in _SharedPath(__file__).resolve().parents
            if (p / "shared" / "digitgen").is_dir()
        )
    ),
)
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
    parser.add_argument(
        "--blender",
        default=shutil.which("blender")
        or "/Applications/Blender.app/Contents/MacOS/Blender",
    )
    parser.add_argument("--config", default="configs/preview.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--count", type=int)
    parser.add_argument("--index", type=int)
    parser.add_argument("--rolling-preview", action="store_true")
    args = parser.parse_args()
    config = load_config(
        (
            ROOT.parent / "shared" / args.config
            if str(args.config).startswith("configs/")
            else ROOT / args.config
        )
    )
    prepare(config)
    output = (args.output or ROOT / config["output"]).resolve()
    command = [
        args.blender,
        "--background",
        "--factory-startup",
        "--python-exit-code",
        "1",
        "--python",
        str(ROOT / "generate.py"),
        "--",
        "--config",
        str(
            (
                ROOT.parent / "shared" / args.config
                if str(args.config).startswith("configs/")
                else ROOT / args.config
            )
        ),
        "--output",
        str(output),
    ]
    for key in ("count", "index"):
        value = getattr(args, key)
        if value is not None:
            command.extend(["--" + key, str(value)])
    if args.rolling_preview:
        command.append("--rolling-preview")
    subprocess.run(command, check=True, cwd=ROOT)
    audit(output)


if __name__ == "__main__":
    main()
