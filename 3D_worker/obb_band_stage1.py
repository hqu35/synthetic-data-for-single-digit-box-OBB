"""One unchanged reference RGB with corrected 3D numeral-band OBBs. Stop after review."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import bpy
from digitgen.band_annotations import project_numeral_bands
from digitgen.export import export_labels,read_labels,svg_overlay,write_json
from industrial_fonts_review import fingerprint


def unchanged_scene_signature():
    data=fingerprint()
    data['shader_values']={m.name:[(n.name,[(s.name,list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value)
        for s in n.inputs if hasattr(s,'default_value')]) for n in m.node_tree.nodes]
        for m in bpy.data.materials if m.use_nodes}
    data['image_pixels']={im.name:hashlib.sha256(bytes(im.packed_file.data)).hexdigest()
        for im in bpy.data.images if im.packed_file}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',default='configs/obb_band_stage1.json')
    parser.add_argument('--recheck',action='store_true',help='Verify current annotations against existing one-sample RGB; render nothing')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    config=json.loads((ROOT/args.config).read_text());out=ROOT/config['output']
    if not args.recheck and out.exists() and any(out.iterdir()):raise ValueError('Choose a new/empty review output directory')
    out.mkdir(parents=True,exist_ok=True)
    source=ROOT/config['source_scene'];bpy.ops.wm.open_mainfile(filepath=str(source))
    scene=bpy.context.scene;camera=scene.camera;register=bpy.data.objects['RegisterHousing']
    bpy.context.view_layer.update();before=unchanged_scene_signature()
    resolution=[scene.render.resolution_x,scene.render.resolution_y]
    if scene.render.resolution_percentage!=100:raise ValueError('Reference must use full saved resolution')
    regions=project_numeral_bands(scene,camera,register,resolution,config['digit_count'])
    after=unchanged_scene_signature()
    if before!=after:raise AssertionError('Annotation projection changed scene appearance or geometry')
    boxes=[r['obb_px'] for r in regions]
    if args.recheck:
        report=json.loads((out/'inspection_report.json').read_text())
        if report['source_scene_sha256']!=hashlib.sha256(source.read_bytes()).hexdigest():
            raise AssertionError('Saved RGB source scene has changed')
        if report['scene_signature_before']!=before:raise AssertionError('Saved RGB model state differs')
        stored=read_labels(out/'000001.txt',resolution)
        if max(abs(a-b) for box,other in zip(boxes,stored) for p,q in zip(box,other) for a,b in zip(p,q))>1e-6:
            raise AssertionError('Current projection no longer matches saved sample labels')
        report['regions']=regions
        report['implementation_sha256']=hashlib.sha256((ROOT/'digitgen/band_annotations.py').read_bytes()).hexdigest()
        report['post_render_annotation_recheck']='passed against current implementation and unchanged scene; zero additional renders'
        write_json(out/'inspection_report.json',report);print('SAVED_SAMPLE_ANNOTATIONS_RECHECKED_WITHOUT_RENDER');return
    labels=out/'000001.txt';export_labels(labels,boxes,resolution)
    reloaded=read_labels(labels,resolution)
    if max(abs(a-b) for box,other in zip(boxes,reloaded) for p,q in zip(box,other) for a,b in zip(p,q))>1e-6:
        raise AssertionError('Saved-label roundtrip mismatch')
    # Exactly one RGB render; camera, seed, lighting, shaders and wheel poses
    # are the saved neutral-glass reference. No construction/randomization.
    scene.render.filepath=str(out/'000001.png');bpy.ops.render.render(write_still=True)
    svg_overlay(out/'000001.png',labels,out/'000001_overlay.svg',resolution)
    if unchanged_scene_signature()!=before:raise AssertionError('Render changed model state')
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'band_annotation_review.blend'))
    source_parameters=json.loads((ROOT/config['source_parameters']).read_text())
    report={'status':'Stage 1 complete; awaiting human approval before Stage 2',
        'rendered_rgb_count':1,'stage2_started':False,'config':config,
        'annotation_semantics':'Visible printed outer numeral-bearing band, including its cream background; clipped by both physical window faces, excluding axial shoulders/pins; one minimum-area enclosing pixel-space rectangle per digit.',
        'classes':{'0':'digit_band'},'digit_sequence':'00054',
        'source_scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_reference_parameters':source_parameters,'resolution':resolution,
        'seed':scene.cycles.seed,'blender_version':bpy.app.version_string,
        'render':{'engine':scene.render.engine,'samples':scene.cycles.samples,'denoising':scene.cycles.use_denoising,
                  'threads':scene.render.threads,'view_transform':scene.view_settings.view_transform,
                  'exposure':scene.view_settings.exposure,'look':scene.view_settings.look},
        'camera':{'name':camera.name,'matrix_world':list(map(list,camera.matrix_world)),
                  'lens_mm':camera.data.lens,'type':camera.data.type},
        'register_matrix_world':list(map(list,register.matrix_world)),
        'scene_signature_before':before,'scene_signature_after':after,
        'geometry_material_atlas_camera_lighting_unchanged':True,'regions':regions,
        'glass_policy':'Preserved native glass. Labels remain direct geometry projections, not image-fitted glyph boxes; small optical shifts remain as documented in the source glass review.',
        'implementation_sha256':hashlib.sha256((ROOT/'digitgen/band_annotations.py').read_bytes()).hexdigest()}
    write_json(out/'inspection_report.json',report);write_json(out/'config.json',config)
    write_json(out/'classes.json',{'0':'digit_band'})
    print('ONE_SAMPLE_OBB_REVIEW_OK',json.dumps({'output':str(out),'boxes':len(regions),
        'mesh_width_ratios':[r['band_to_slot_width_ratio'] for r in regions]},indent=2))


if __name__=='__main__':main()
