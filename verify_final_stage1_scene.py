"""Reload the saved review .blend and verify actual shader and rolling OBB invariance."""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import bpy
from mathutils import Vector
from stage1_raised_band import show
from digitgen.scene import project_regions
from digitgen.geometry import minimum_rectangle
from digitgen.export import write_json
from digitgen.pin_calibration import calibrate_pins
from digitgen.raised_mechanics import rebuild_pins
from digitgen.pin_visibility import measure_pins,inside


def aperture_intervals(c,p,scene,camera,resolution):
    """Bisect actual projected front/back aperture containment of virtual pins."""
    deps=bpy.context.evaluated_depsgraph_get()
    matrix=camera.calc_matrix_camera(deps,x=resolution[0],y=resolution[1])@camera.matrix_world.inverted()
    openings=project_regions(scene,camera,[w['center_x'] for w in p['wheels']],p['slot_width'],p['slot_height'],p['wheel_radius']+c['aperture_standoff'],c['frame_depth'],resolution)
    def pixel(point):
        q=matrix@Vector((*point,1));return [(.5+.5*q.x/q.w)*resolution[0],(.5-.5*q.y/q.w)*resolution[1]]
    result=[]
    for i,opening in enumerate(openings):
        x=p['wheels'][i]['center_x']+p['slot_width']*.35+c['edge_rim_width']+c['pin_length']/2
        def contained(angle,whole):
            y,z=c['pin_radial_position']*math.sin(angle),c['pin_radial_position']*math.cos(angle)
            if not whole:return inside(pixel((x,y,z)),opening)
            return all(inside(pixel((x+dx,y+c['pin_radius']*math.sin(a*math.pi/8),z+c['pin_radius']*math.cos(a*math.pi/8))),opening)
                       for dx in (-c['pin_length']/2,c['pin_length']/2) for a in range(16))
        limits={}
        for whole,label in [(False,'rim_center'),(True,'whole_pin_silhouette')]:
            edges=[]
            for sign in (-1,1):
                lo,hi=0,math.pi/2
                for _ in range(32):
                    mid=(lo+hi)/2
                    if contained(sign*mid,whole):lo=mid
                    else:hi=mid
                edges.append(sign*math.degrees(lo))
            limits[label+'_front_angle_interval_deg']=edges
        result.append({'wheel':i,**limits})
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='outputs/stage1_final_refinement')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    out=(ROOT/args.output).resolve();report=json.loads((out/'inspection_report.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(out/'final_stage1_review.blend'))
    c=report['config'];p=report['parameters'];scene=bpy.context.scene
    camera=bpy.data.objects['A_three_visible_pins'];scene.camera=camera;show(c['views']['single'],True)
    resolution=c['views']['single']['resolution'];scene.render.resolution_x,scene.render.resolution_y=resolution
    parent=bpy.data.objects['wheel_2_axle'];original=parent.rotation_euler.x
    boxes=[]
    for t in (0,.25,.5,.75):
        parent.rotation_euler.x=(4+t)*3.141592653589793/5;bpy.context.view_layer.update()
        boundary=project_regions(scene,camera,[0],p['slot_width'],p['slot_height'],p['wheel_radius']+c['aperture_standoff'],c['frame_depth'],resolution)[0]
        boxes.append(minimum_rectangle(boundary)[0])
    if any(box!=boxes[0] for box in boxes[1:]):raise AssertionError('Rolling changed physical slot OBB')
    parent.rotation_euler.x=original;bpy.context.view_layer.update()
    mat=bpy.data.objects['wheel_2_raised_band'].data.materials[0];nodes=mat.node_tree.nodes
    shader=nodes['Principled BSDF']
    if shader.inputs['Metallic'].default_value!=0 or abs(shader.inputs['IOR'].default_value-1.5)>1e-6:raise AssertionError('Unexpected dielectric material')
    if abs(nodes['Ink / substrate roughness'].inputs[2].default_value[0]-.3)>1e-6:raise AssertionError('Ink roughness was not saved')
    if not mat.get('ink_gloss_enabled'):raise AssertionError('Saved model lacks glossy ink')
    if nodes['Cylindrical ink mask'].image.packed_file is None:raise AssertionError('Review scene is missing packed ink texture')
    if shader.inputs.get('Specular IOR Level') is None:raise AssertionError('Installed Blender lacks the requested supported IOR level socket')
    four=dict(c);four.update(calibrate_pins(c,4));rebuild_pins(four,report['layout'])
    scene.camera=bpy.data.objects['C_fixed_00054_register'];show(c['views']['row'])
    scene.render.resolution_x,scene.render.resolution_y=c['views']['row']['resolution']
    four_row=measure_pins(four,p,scene.camera,c['views']['row']['resolution'],list(range(5)))
    intervals=aperture_intervals(c,p,scene,scene.camera,c['views']['row']['resolution'])
    result={'status':'passed','blender_version':bpy.app.version_string,'saved_scene_reloaded':True,
            'rolling_obb_coordinates_identical':True,'single_slot_obb_px':boxes[0],
            'checked_transition_progress':[0,.25,.5,.75],'ink_texture_packed':True,
            'ink_roughness':nodes['Ink / substrate roughness'].inputs[2].default_value[0],
            'metallic':0,'ior':1.5,'specular_ior_level_supported':True,
            'four_pin_row_projection_counts':[w['actually_visible_count'] for w in four_row],
            'four_pin_row_projection_records':four_row,
            'actual_projected_aperture_angular_intervals':intervals,
            'stage':'Stage 1 only; no additional renders or training samples were created by this verification'}
    write_json(out/'saved_scene_verification.json',result)
    print(json.dumps({key:value for key,value in result.items() if key!='four_pin_row_projection_records'},indent=2))


if __name__=='__main__':main()
