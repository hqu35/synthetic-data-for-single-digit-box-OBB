"""No-render analytic invariants for the axis-aligned protective-cover diagnostic.
Run Blender --background --python tests/optics_invariants_blender.py.
"""
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from digitgen.glass import refracted_projection

s=bpy.context.scene
s.render.resolution_x=1200;s.render.resolution_y=800;s.render.resolution_percentage=100
cam_data=bpy.data.cameras.new('Independent optics test camera')
cam=bpy.data.objects.new('Independent optics test camera',cam_data);s.collection.objects.link(cam)
s.camera=cam;cam_data.lens=50
res=[1200,800]
d={'thickness':.1,'back_z':2.,'front_z':2.1,'width':20.,'height':20.}
checks=[]

def plain(p):
    q=world_to_camera_view(s,cam,Vector(p))
    return Vector((q.x*res[0],(1-q.y)*res[1]))

cam.location=(0,0,10);cam.rotation_euler=(0,0,0);bpy.context.view_layer.update()
for ior in [1.,1.33,1.5,2.]:
    q,covered=refracted_projection((0,0,0),cam,s,res,d,ior)
    error=(Vector(q)-plain((0,0,0))).length
    assert error<1e-6 and covered,(ior,error)
checks.append('All IORs preserve the normal-incidence central ray')
for location in [(0,0,10),(4,2,10),(-4,-2,10)]:
    cam.location=location
    cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()
    for point in [(0,0,0),(1,.4,.3),(-1,-.5,1.2)]:
        q,covered=refracted_projection(point,cam,s,res,d,1.)
        error=(Vector(q)-plain(point)).length
        assert error<.002 and covered,(location,point,error)
checks.append('IOR 1.0 agrees with unrefracted perspective projection at nine off-axis combinations')
cam.location=(0,0,10);cam.rotation_euler=(0,0,0);bpy.context.view_layer.update()
q1,_=refracted_projection((1,0,0),cam,s,res,d,1.)
q15,_=refracted_projection((1,0,0),cam,s,res,d,1.5)
assert q15[0]>q1[0] and abs(q15[1]-q1[1])<1e-5
checks.append('IOR 1.5 moves an off-axis target outward relative to IOR 1.0 as expected for a parallel slab')
narrow=dict(d,width=.01,height=.01)
_,covered=refracted_projection((1,0,0),cam,s,res,narrow,1.5)
assert not covered
checks.append('A path outside the finite rectangular cover is rejected')
print(json.dumps({'independent_no_render_optics_invariants':'passed','checks':checks},indent=2),flush=True)
