"""Render one tightly framed register preview; never resume the dataset batch."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import bpy
from digitgen.experiment1_scene import orient,immutable_signature
from digitgen.band_annotations import project_numeral_bands
from digitgen.scene import project
from digitgen.geometry import hull,area
from digitgen.export import write_json,export_labels,svg_overlay


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default='configs/tight_framing_preview.json')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    config=json.loads((ROOT/args.config).read_text());out=ROOT/config['output']
    if out.exists() and any(out.iterdir()):raise ValueError('Use a new/empty preview output directory')
    out.mkdir(parents=True,exist_ok=True)
    source=ROOT/config['source_scene'];bpy.ops.wm.open_mainfile(filepath=str(source))
    scene=bpy.context.scene;camera=scene.camera;signature=immutable_signature()
    camera.location=config['camera_position'];orient(camera,config['camera_target'],config['camera_roll_degrees'])
    camera.data.lens=100;camera.data.dof.use_dof=False
    scene.render.resolution_x,scene.render.resolution_y=config['resolution'];scene.render.resolution_percentage=100
    scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
    scene.cycles.samples=config['samples'];scene.cycles.seed=config['seed'];scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED';scene.render.threads=config['threads']
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='8'
    # Register footprint includes the continuous glass and its narrow external
    # seat. Large surrounding inspection/background planes are excluded.
    front_objects=[o for o in scene.objects if o.type=='MESH' and
                   (o.name=='Continuous_glass_cover' or o.name.startswith('glass_seat_'))]
    world_vertices=[o.matrix_world@v.co for o in front_objects for v in o.data.vertices]
    width,height=config['resolution'];target=config['target_register_image_area_fraction']
    for _ in range(3):
        bpy.context.view_layer.update()
        footprint=hull(project(scene,camera,world_vertices,config['resolution']))
        fraction=area(footprint)/(width*height)
        camera.data.lens*=((target/fraction)**.5)
    bpy.context.view_layer.update()
    footprint=hull(project(scene,camera,world_vertices,config['resolution']))
    fraction=area(footprint)/(width*height)
    if not .90<=fraction<=.95:raise AssertionError('Register footprint does not satisfy requested occupancy')
    if any(not 0<x<width or not 0<y<height for x,y in footprint):raise AssertionError('Register is cropped by image frame')
    regions=project_numeral_bands(scene,camera,bpy.data.objects['RegisterHousing'],config['resolution'])
    if immutable_signature()!=signature:raise AssertionError('Framing changed mechanics, atlas or glass')
    scene.render.filepath=str(out/'register_closeup.png');bpy.ops.render.render(write_still=True)
    export_labels(out/'register_closeup.txt',[r['obb_px'] for r in regions],config['resolution'])
    svg_overlay(out/'register_closeup.png',out/'register_closeup.txt',out/'register_closeup_overlay.svg',config['resolution'])
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'tight_framing_preview.blend'))
    report={'status':'One preview rendered; dataset batch remains paused','config':config,
        'render_count':1,'dataset_resumed':False,'true_digit_sequence':'00054',
        'source_scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'preserved_geometry_atlas_glass_signature':signature,
        'register_footprint_area_fraction':fraction,'background_area_fraction':1-fraction,
        'occupancy_definition':'Image area inside the projected outer glass/seat silhouette divided by total image area; the mechanical register and its viewing window count as register.',
        'register_footprint_polygon_px':footprint,'register_front_objects':[o.name for o in front_objects],
        'camera':{'position':list(camera.location),'matrix_world':list(map(list,camera.matrix_world)),
                  'focal_length_mm':camera.data.lens,'fov_degrees':__import__('math').degrees(camera.data.angle),
                  'sensor_width_mm':camera.data.sensor_width},
        'blender_version':bpy.app.version_string,'regions':regions,
        'source_reference_parameters':json.loads((ROOT/config['source_parameters']).read_text()),
        'scope':'Camera framing and output aspect only. No mechanical, font, transition, light or shader changes; no image crop or resize.'}
    write_json(out/'inspection_report.json',report);write_json(out/'config.json',config)
    print('TIGHT_FRAMING_PREVIEW_OK',json.dumps({'register_area_fraction':fraction,'background_area_fraction':1-fraction,
        'focal_length_mm':camera.data.lens,'obb_count':len(regions)},indent=2))


if __name__=='__main__':main()
