"""Inspect 3D digit 4 to 5 transition at five wheel-angle checkpoints."""

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
import copy, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import bpy
from scene.scene_core import (
    setup,
    CONFIG,
    SOURCE_PARAMS,
    ROLLING_ATLAS_CONFIG,
    sha,
)
from digitgen.assets import texture_spec, verify_spec
from digitgen.export import write_json, export_labels
from digitgen.camera_appearance import process_image

out = ROOT / "outputs/rolling_gap_review"
if out.exists() and any(out.iterdir()):
    raise ValueError("Output directory exists")
for sub in ("images", "labels", "metadata"):
    (out / sub).mkdir(parents=True, exist_ok=True)
old = json.loads(
    (ROOT / "outputs/scratch_multi_version/metadata/000001.json").read_text()
)
base = {
    k: old[k] for k in ("sample_id", "digits", "transitions", "parameters")
}
c = json.loads(CONFIG.read_text())
c["count"] = 100
c["camera"].pop("pose_overrides", None)
c["resolution"] = [1200, 460]
source = json.loads(SOURCE_PARAMS.read_text())
rolling = json.loads(ROLLING_ATLAS_CONFIG.read_text())
atlas = texture_spec(rolling)
verify_spec(atlas)
for state in (0, 0.1, 0.2, 0.25, 0.5, 0.75, 1):
    item = copy.deepcopy(base)
    item["digits"] = "00500" if state == 1 else "00400"
    item["transitions"] = [0, 0, state if state < 1 else 0, 0, 0]
    scene, states, regions, resolved, framing = setup(
        item,
        c,
        source,
        0.75,
        ROOT.parent / "shared" / atlas["path"],
        rolling["geometry"],
    )
    image = out / "images" / f"transition_{round(state * 100):03}.png"
    label = out / "labels" / f"transition_{round(state * 100):03}.txt"
    scene.render.filepath = str(image)
    bpy.ops.render.render(write_still=True)
    processing = copy.deepcopy(old["camera_processing"])
    process_image(image, image, processing)
    export_labels(label, [r["obb_px"] for r in regions], c["resolution"])
    write_json(
        out / "metadata" / f"transition_{round(state * 100):03}.json",
        {
            "transition_4_to_5": state,
            "digits": item["digits"],
            "wheel_states": states,
            "atlas": atlas,
            "camera_processing": processing,
            "regions": regions,
            "framing": framing,
            "image_sha256": sha(image),
            "label_sha256": sha(label),
        },
    )
    print("ROLLING_REVIEW_OK", state, flush=True)
print("ROLLING_REVIEW_COMPLETE", flush=True)
