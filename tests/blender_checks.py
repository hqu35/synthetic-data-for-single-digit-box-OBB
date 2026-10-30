"""Real-Blender geometry regression checks; no rendering required."""
import copy
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import bpy
from digitgen.config import load_config
from digitgen.geometry import minimum_rectangle, validate_boxes
from digitgen.sampling import sample_parameters, wheel_state
from digitgen.scene import create_scene, project_regions

c = load_config(ROOT/'configs/preview.json')
# Both signs/projection types, including the former camera-solver regression.
for index in (0,1,10,17,24):
    # Very narrow gaps with oblique perspective can expose a cylinder's axial
    # edge. Exercise the same explicit rejection/regeneration policy as production.
    for attempt in range(c['max_attempts']):
        p = sample_parameters(c,index,attempt)
        try:
            scene, boxes, boundaries = create_scene(c,p)
        except ValueError as exc:
            print('EXPECTED_GEOMETRY_REJECTION',index,attempt,str(exc),flush=True)
            continue
        break
    else:raise AssertionError('No valid scene within bounded retries')
    validate_boxes(boxes,boundaries,c['resolution'],p['requested_angle_deg'],c['rotation'])
    if abs(p['camera']['solved_roll_deg'])>25:
        raise AssertionError('Spurious camera axis flip')
    body=bpy.data.objects['wheel_0_cylinder']
    if any('numeral_' in o.name for o in bpy.context.scene.objects):
        raise AssertionError('Raised text meshes must not exist')
    for vertex in body.data.vertices:
        if abs(math.hypot(vertex.co.y,vertex.co.z)-p['wheel_radius'])>1e-5:
            raise AssertionError('Wheel body is not cylindrical')
    uv=body.data.uv_layers['Circumference_Axial']
    for j,face in enumerate(body.data.polygons[:p['mechanics']['radial_segments']]):
        first=uv.data[face.loop_indices[0]].uv
        if abs(first.x-(j/p['mechanics']['radial_segments']+.05))>1e-6:
            raise AssertionError('Cylindrical UV calibration changed')
    pins=[o for o in bpy.context.scene.objects if o.name.startswith('wheel_0_pin_')]
    if len(pins)!=p['mechanics']['pin_count'] or any(o.parent!=bpy.data.objects['wheel_0_axle'] for o in pins):
        raise AssertionError('Pins must rotate as part of their wheel')
    material=body.data.materials[0];nodes=material.node_tree.nodes;links=material.node_tree.links
    for label,kind,scale in [('Noise A','FBM',100),('Noise B','FBM',20),('Noise C','MULTIFRACTAL',30)]:
        if nodes[label].noise_type!=kind or nodes[label].inputs['Scale'].default_value!=scale:
            raise AssertionError('Supplied guide noise settings changed')
        if not any(l.from_node==nodes['Shared Mapping'] and l.to_socket==nodes[label].inputs['Vector'] for l in links):
            raise AssertionError('Noise vectors must share the Mapping node')
    if nodes['Noise B x Noise C'].operation!='MULTIPLY' or not nodes['Inverted micro bump'].invert:
        raise AssertionError('Guide requires Math Multiply and inverted Bump')
    for preset in ('reference_dark_plastic','meter_cream_matte'):
        from digitgen.materials import plastic
        test=plastic('verify '+preset,p['appearance'],preset=preset)
        if preset=='reference_dark_plastic':
            bump=test.node_tree.nodes['Inverted micro bump']
            if abs(bump.inputs['Strength'].default_value-.05)>1e-6 or bump.inputs['Distance'].default_value!=1:
                raise AssertionError('Reference reproduction bump settings changed')
    original = copy.deepcopy(boxes)
    for digit in range(10):
        for progress in (0,.25,.5,.75,.999999):
            state = wheel_state(0,digit,progress)
            bpy.data.objects['wheel_0_axle'].rotation_euler.x = state['wheel_rotation']
            bpy.context.view_layer.update()
            projected = project_regions(scene,scene.camera,[w['center_x'] for w in p['wheels']],p['slot_width'],p['slot_height'],p['aperture_z'],p['aperture_frame_depth'],c['resolution'])
            fitted = [minimum_rectangle(b)[0] for b in projected]
            if max(abs(a-b) for box,ref in zip(fitted,original) for point,rpoint in zip(box,ref) for a,b in zip(point,rpoint))>1e-5:
                raise AssertionError('OBB changed with wheel axle state')
    print('BLENDER_GEOMETRY_OK',index,flush=True)
print('PASS: cylindrical UVs, guide shader graph, pin attachment, roll calibration, and 250 wheel-state/OBB invariance checks')
