"""Native Blender font-only review against the approved saved mechanical scene.

Run after python3 prepare_font_review.py. Changes only ink image references;
all geometry, camera transforms, lights, shader nodes and cell spacing are frozen.
"""
import hashlib
import json
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from digitgen.assets import texture_spec, verify_spec
OUT=ROOT/'outputs/industrial_fonts_review'
SOURCE=ROOT/'outputs/stage1_final_refinement/final_stage1_review.blend'


def fingerprint():
    mesh={}
    for o in bpy.data.objects:
        if o.type=='MESH':
            mesh[o.name]={'matrix':list(map(list,o.matrix_world)),
                'vertices':hashlib.sha256(repr([tuple(v.co) for v in o.data.vertices]).encode()).hexdigest(),
                'polygons':hashlib.sha256(repr([tuple(p.vertices) for p in o.data.polygons]).encode()).hexdigest(),
                'hide_render':o.hide_render}
    s=bpy.context.scene;cam=s.camera
    lights={o.name:{'matrix':list(map(list,o.matrix_world)),'energy':o.data.energy,
        'color':list(o.data.color),'size':o.data.size,'type':o.data.type}
        for o in bpy.data.objects if o.type=='LIGHT'}
    return {'meshes':mesh,'camera':{'name':cam.name,'matrix':list(map(list,cam.matrix_world)),
        'lens':cam.data.lens,'type':cam.data.type},'lights':lights,
        'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],
        'world':[(n.name,[(i.name,list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value) for i in n.inputs if hasattr(i,'default_value')]) for n in s.world.node_tree.nodes],
        'shader_links':{m.name:sorted((l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links) for m in bpy.data.materials if m.use_nodes}}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    s=bpy.context.scene;s.cycles.device='CPU';s.cycles.seed=0;s.cycles.use_animated_seed=False
    s.render.threads_mode='FIXED';s.render.threads=4
    baseline=fingerprint();entries={}
    # Condensed is supplementary; main comparison remains the two requested fonts.
    for preset in ['din1451_like','ocr_b','din_condensed_like']:
        c=json.loads((OUT/f'{preset}_config.json').read_text())
        spec=texture_spec(c);verify_spec(spec)
        image=bpy.data.images.load(str(ROOT/spec['path']),check_existing=True)
        image.colorspace_settings.name='Non-Color'
        changed=[]
        materials={bpy.data.objects[f'wheel_{i}_raised_band'].data.materials[0] for i in range(5)}
        for mat in materials:
            for n in mat.node_tree.nodes:
                if n.type=='TEX_IMAGE' and n.image:
                    n.image=image;changed.append([mat.name,n.name])
        assert changed,'No ink nodes found'
        assert fingerprint()==baseline,'Font preview altered frozen scene properties'
        s.render.filepath=str(OUT/f'{preset}_00054.png')
        bpy.ops.render.render(write_still=True)
        for i in bpy.data.images:
            if i.source=='FILE' and not i.packed_file:i.pack()
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{preset}_review.blend'))
        entries[preset]={'config':c,'texture':spec,'changed_nodes':changed,'seed':s.cycles.seed,
            'samples':s.cycles.samples,'same_geometry_camera_lighting_shader_links':fingerprint()==baseline,
            'png':f'{preset}_00054.png','blend':f'{preset}_review.blend'}
    report={'status':'Industrial typography review only; STOP for human review',
        'blender_version':bpy.app.version_string,'source_scene':str(SOURCE.relative_to(ROOT)),
        'source_scene_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'scene_invariants':baseline,'candidates':entries,
        'unchanged':{'digits':'0123456789','angular_pitch_degrees':36,'sequence':'00054',
            'transition_progress':[0,0,0,0,.05],'cell_spacing':True,'aperture_mapping':True},
        'unresolved':['Excess blank circumferential spacing between digits is intentionally unchanged.',
            'Rolling-transition midpoint is intentionally deferred.','Fonts are exploratory candidates, not verified manufacturer matches.',
            'Existing atlas generator normalizes each font to the same maximum glyph width and numeral height; condensed font does not shrink the band or cell.'],
        'datasets_generated':False}
    (OUT/'inspection_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'completed':list(entries),'frozen_scene_verified':True}))

if __name__=='__main__':main()
