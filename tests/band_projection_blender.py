"""No-render integration tests: actual mesh projection under 3D camera/register transforms."""
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import bpy
from mathutils import Matrix,Vector,Quaternion,Euler
from digitgen.band_annotations import project_numeral_bands
from digitgen.geometry import area

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'outputs/glass_review/protective_glass_review.blend'))
scene=bpy.context.scene;cam=scene.camera;root=bpy.data.objects['RegisterHousing'];res=[1600,540]
original_cam=cam.matrix_world.copy();original_root=root.matrix_world.copy();original_lens=cam.data.lens
baseline=project_numeral_bands(scene,cam,root,res)
assert len(baseline)==5
scene.render.resolution_y=700
try:
    project_numeral_bands(scene,cam,root,res)
except ValueError as exc:
    assert 'resolution/aspect' in str(exc)
else:
    raise AssertionError('Mismatched scene aspect was not rejected')
scene.render.resolution_y=res[1]
for r in baseline:
    assert abs(r['band_to_slot_width_ratio']-.7)<1e-6
    assert abs(r['left_margin_fraction']-.15)<1e-6 and abs(r['right_margin_fraction']-.15)<1e-6
    assert .68<r['projected_obb_width_to_slot_ratio']<.72
# Transform camera and entire register together: the projection must be invariant.
rigid=Matrix.Translation((1,-2,.3))@Euler((.15,-.10,.21)).to_matrix().to_4x4()
root.matrix_world=rigid@original_root;cam.matrix_world=rigid@original_cam;bpy.context.view_layer.update()
covariant=project_numeral_bands(scene,cam,root,res)
max_error=max(abs(a-b) for p,q in zip(baseline,covariant) for v,w in zip(p['obb_px'],q['obb_px']) for a,b in zip(v,w))
assert max_error<.005,max_error
root.matrix_world=original_root;cam.matrix_world=original_cam;bpy.context.view_layer.update()
checks=[]
for yaw,pitch,roll,register_euler,lens_factor,distance in [
    (8,-4,15,(0,0,0),.60,16),(-9,5,-18,(0,0,0),.58,17),
    (6,3,10,(.04,-.05,.06),.60,16),(-5,-3,28,(-.03,.02,-.04),.48,17)]:
    root.matrix_world=Euler(register_euler).to_matrix().to_4x4()
    target=Vector((0,0,1.25));ya,pi=math.radians(yaw),math.radians(pitch)
    cam.location=target+distance*Vector((math.sin(ya)*math.cos(pi),math.sin(pi),math.cos(ya)*math.cos(pi)))
    forward=(target-cam.location).normalized();right=forward.cross(Vector((0,1,0))).normalized();up=right.cross(forward)
    base=Matrix((right,up,-forward)).transposed().to_quaternion()
    cam.rotation_mode='QUATERNION';cam.rotation_quaternion=base@Quaternion((0,0,1),math.radians(roll));cam.data.lens=original_lens*lens_factor
    bpy.context.view_layer.update();regions=project_numeral_bands(scene,cam,root,res)
    assert len(regions)==5
    assert any(abs(a-b)>5 for p,q in zip(baseline,regions) for v,w in zip(p['obb_px'],q['obb_px']) for a,b in zip(v,w))
    for r in regions:
        # Independent dense orientation sweep: no sampled enclosing rectangle
        # may beat the edge-based minimum-area fit. It must also be tight.
        pts=r['visible_boundary_px']; fitted=area(r['obb_px'])
        sampled=[]
        for degree in range(0,1800):
            t=degree*math.pi/1800;c,s=math.cos(t),math.sin(t)
            u=[p[0]*c+p[1]*s for p in pts];v=[-p[0]*s+p[1]*c for p in pts]
            sampled.append((max(u)-min(u))*(max(v)-min(v)))
        assert fitted<=min(sampled)+1e-4,(fitted,min(sampled))
        assert fitted/min(sampled)>.99
        assert .55<r['projected_obb_width_to_slot_ratio']<.90
    checks.append({'camera_yaw_pitch_roll_deg':[yaw,pitch,roll],
                   'register_euler_radians':register_euler,'distance':distance,'lens_factor':lens_factor,
                   'digit_boxes':5,'min_boundary_to_obb_area_ratio':min(r['checks']['boundary_to_obb_area_ratio'] for r in regions)})
print('BAND_PROJECTION_TESTS_OK',json.dumps({'status':'passed','renders':0,
    'joint_camera_register_transform_max_error_px':max_error,'poses':checks},indent=2))
