"""Shared 3D scene setup, camera sampling and projection."""

# Load the single shared package without worker-local asset links.
import sys as _shared_sys
from pathlib import Path as _SharedPath

_shared_sys.path.insert(
    0,
    str(
        next(
            p / 'shared'
            for p in _SharedPath(__file__).resolve().parents
            if (p / 'shared' / 'digitgen').is_dir()
        )
    ),
)
import argparse, copy, hashlib, json, math, random, shutil, sys, time, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / 'shared'))
import bpy
from digitgen.experiment1_sampling import sample_parameters
from digitgen.experiment1_scene import (
    apply_parameters,
    fit_register_camera,
)
from digitgen.band_annotations import project_numeral_bands
from digitgen.sampling import wheel_state
from digitgen.export import export_labels, write_json
from digitgen.camera_appearance import (
    process_image,
    blur_sigma_from_percent,
)
from digitgen.assets import texture_spec, verify_spec
from digitgen.shear import (
    make_shear_plan,
    apply_to_file,
    SHEAR_BUCKETS,
)

CONFIG = (
    ROOT.parent / 'shared/configs/perspective_review.json'
)
SOURCE = (
    ROOT
    / 'outputs/glass_review/protective_glass_review.blend'
)
SOURCE_PARAMS = (
    ROOT
    / 'outputs/glass_review/02_glass_neutral_parameters.json'
)
ROLLING_ATLAS_CONFIG = (
    ROOT.parent
    / 'shared/configs/rolling_numerals_atlas.json'
)


def sha(path):
    return hashlib.sha256(
        Path(path).read_bytes()
    ).hexdigest()


def plan_item(config, index):
    p = sample_parameters(config, index, 0)
    rng = random.Random(p['seed'] + 721003)
    # Unique across all examples, including leading zeros.
    digit_pool = list(range(100000))
    random.Random(20261031).shuffle(digit_pool)
    digits = f'{digit_pool[index-1]:05d}'
    transition = [0.0] * 5
    if index % 5 != 0:
        transition[index % 5] = [
            0.12,
            0.25,
            0.4,
            0.5,
            0.65,
            0.8,
        ][(index // 5) % 6]
        if index % 4 == 0:
            transition[(index + 2) % 5] = [0.2, 0.5, 0.75][
                (index // 4) % 3
            ]
    # A range of moderate perspective while maintaining tight framing.
    yaw = rng.choice([-1, 1]) * rng.uniform(8, 15)
    p['camera'].update(
        yaw_deg=yaw,
        pitch_deg=rng.uniform(-3, 3),
        roll_deg=0,
        distance=rng.uniform(7.5, 8.0),
        target_register_area_fraction=0.905,
    )
    return {
        'sample_id': f'{index:06d}',
        'digits': digits,
        'transitions': transition,
        'parameters': p,
    }


def setup(
    item,
    config,
    source,
    width_scale=0.75,
    atlas_path=None,
    rolling_geometry=None,
):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    if rolling_geometry:
        radius_scale = rolling_geometry[
            'wheel_radius_scale'
        ]
        window_scale = rolling_geometry[
            'window_height_scale'
        ]
        # Shrink each wheel radially around its axle, then move
        # its axle forward
        # to keep the raised printed surface at the existing glass clearance.
        for i in range(5):
            axle = bpy.data.objects[f'wheel_{i}_axle']
            axle.scale.y = radius_scale
            axle.scale.z = radius_scale
            axle.location.z = (
                1 - radius_scale
            ) * rolling_geometry['original_band_radius']
        # Scale the window frame's vertical dimensions around its center.
        for obj in bpy.context.scene.objects:
            if obj.name.startswith('front_review_'):
                obj.location.y *= window_scale
                obj.scale.y *= window_scale
    if atlas_path is not None:
        atlas = bpy.data.images.load(
            str(atlas_path), check_existing=True
        )
        atlas.colorspace_settings.name = 'Non-Color'
        for i in range(5):
            material = bpy.data.objects[
                f'wheel_{i}_raised_band'
            ].data.materials[0]
            node = material.node_tree.nodes.get(
                'Cylindrical ink mask'
            )
            if node is None:
                raise ValueError(
                    'Numeral band is missing its cylindrical ink mask'
                )
            node.image = atlas
    # Scale the complete register along the axle: wheel widths, pitch, gaps,
    # frame and glass all stay mechanically aligned. Height and
    # depth stay fixed.
    bpy.data.objects['RegisterHousing'].scale.x = (
        width_scale
    )
    bpy.context.view_layer.update()
    resolved = apply_parameters(
        config, item['parameters'], source
    )
    framing = fit_register_camera(
        config, item['parameters']
    )
    states = [
        wheel_state(i, int(d), t)
        for i, (d, t) in enumerate(
            zip(item['digits'], item['transitions'])
        )
    ]
    rotation_sign = (
        rolling_geometry.get('rotation_sign', 1)
        if rolling_geometry
        else 1
    )
    if rotation_sign not in (-1, 1):
        raise ValueError('rotation_sign must be -1 or 1')
    for state in states:
        state['wheel_rotation'] *= rotation_sign
        state['rotation_sign'] = rotation_sign
        bpy.data.objects[
            f"wheel_{state['index']}_axle"
        ].rotation_euler.x = state['wheel_rotation']
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    scene.cycles.seed = (
        item['parameters']['seed'] % 2147483647
    )
    regions = project_numeral_bands(
        scene,
        scene.camera,
        bpy.data.objects['RegisterHousing'],
        config['resolution'],
    )
    for region in regions:
        for x, y in region['obb_px']:
            if not (
                0 <= x <= config['resolution'][0]
                and 0 <= y <= config['resolution'][1]
            ):
                raise ValueError('OBB outside image')
    return scene, states, regions, resolved, framing
