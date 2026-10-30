"""Actual Blender pin visibility through a projected solid aperture."""
import math
import bpy
from mathutils import Vector
from .scene import project_regions


def inside(point,polygon,tolerance=1e-5):
    return all((b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])>=-tolerance
               for a,b in zip(polygon,polygon[1:]+polygon[:1]))


def first_render_hit(scene,deps,origin,direction):
    # Blender scene ray_cast includes meshes hidden only from the renderer.
    # Skip their entry/exit faces instead of treating inactive review masks as
    # physical occluders in a different view.
    for _ in range(40):
        hit,location,normal,index,obj,matrix=scene.ray_cast(deps,origin,direction)
        if not hit:return None
        if not obj.hide_render:return obj.name
        origin=location+direction*.0001
    raise ValueError('Too many hidden review surfaces along visibility ray')


def measure_pins(c,p,camera,resolution,wheel_indices,require_target=True):
    scene=bpy.context.scene;bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
    projection=camera.calc_matrix_camera(deps,x=resolution[0],y=resolution[1])@camera.matrix_world.inverted()
    def project(point):
        q=projection@Vector((*point,1));return [(.5+.5*q.x/q.w)*resolution[0],(.5-.5*q.y/q.w)*resolution[1]]
    z=p['wheel_radius']+c['aperture_standoff']
    openings=project_regions(scene,camera,[p['wheels'][i]['center_x'] for i in wheel_indices],p['slot_width'],p['slot_height'],z,c['frame_depth'],resolution)
    reports=[]
    for i,opening in zip(wheel_indices,openings):
        records=[]
        for pin in sorted((o for o in scene.objects if o.name.startswith(f'wheel_{i}_pin_')),key=lambda o:o.name):
            center=pin.matrix_world.translation.copy();pixel=project(center)
            vertices=[pin.matrix_world@v.co for v in pin.data.vertices]
            pixels=[project(v) for v in vertices]
            center_inside=inside(pixel,opening)
            entirely_inside=all(inside(v,opening) for v in pixels)
            any_inside=any(inside(v,opening) for v in pixels) or center_inside
            front=center.z>0
            visible=0;attempted=0
            if any_inside:
                local_camera=pin.matrix_world.inverted()@camera.location
                beta=math.atan2(local_camera.y,local_camera.z)
                for x in (-c['pin_length']*.25,0,c['pin_length']*.25):
                    for delta in (-.4,0,.4):
                        q=pin.matrix_world@Vector((x,c['pin_radius']*math.sin(beta+delta),c['pin_radius']*math.cos(beta+delta)))
                        if not inside(project(q),opening):continue
                        attempted+=1;direction=(q-camera.location).normalized()
                        if first_render_hit(scene,deps,camera.location.copy(),direction)==pin.name:visible+=1
            records.append({'name':pin.name,'front_half':front,'center_projected_inside':center_inside,
                'silhouette_entirely_in_aperture':entirely_inside,'projected_center_px':pixel,
                'projected_bounds_px':[min(v[0] for v in pixels),min(v[1] for v in pixels),max(v[0] for v in pixels),max(v[1] for v in pixels)],
                'rays_tested':attempted,'rays_first_hitting_this_pin':visible,
                'actually_visible':visible>=max(1,attempted//2) if attempted else False})
        visible=sorted([r for r in records if r['actually_visible']],key=lambda r:r['projected_center_px'][1])
        spacing=[math.dist(a['projected_center_px'],b['projected_center_px']) for a,b in zip(visible,visible[1:])]
        separation=[b['projected_bounds_px'][1]-a['projected_bounds_px'][3] for a,b in zip(visible,visible[1:])]
        target=c['target_visible_pins']
        if require_target:
            if len(visible)!=target or any(not r['silhouette_entirely_in_aperture'] for r in visible):
                raise ValueError(f'Wheel {i}: {len(visible)} visible pins, target {target}; clipping or obstruction remains')
            if min(separation)<3:raise ValueError('Projected pins merge or lack three-pixel separation')
            if max(spacing)/min(spacing)>1.12:raise ValueError('Projected pin spacing is not approximately uniform')
            if min(r['projected_bounds_px'][3]-r['projected_bounds_px'][1] for r in visible)<5:
                raise ValueError('Pins too small at final image resolution')
        reports.append({'wheel':i,'total_pins':len(records),
            'geometric_front_center_count':sum(r['front_half'] and r['center_projected_inside'] for r in records),
            'projected_center_count_including_occluded_back_pins':sum(r['center_projected_inside'] for r in records),
            'actually_visible_count':len(visible),'projected_positions_px':[r['projected_center_px'] for r in visible],
            'adjacent_projected_spacing_px':spacing,'adjacent_silhouette_clearance_px':separation,
            'spacing_ratio':max(spacing)/min(spacing) if spacing and min(spacing)>0 else None,
            'all_visible_pins_fully_within_aperture':all(r['silhouette_entirely_in_aperture'] for r in visible),
            'pins':records})
    return reports
