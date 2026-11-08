"""Finite-aperture pin density calibration; no random sampling."""
import math


def calibrate_pins(c,target=None):
    target=target or c['target_visible_pins']
    if target not in (3,4):raise ValueError('target_visible_pins must be 3 or 4')
    radius=c['pin_radial_position'];pin=c['pin_radius']
    # Require complete silhouettes inside the opening, with a physical safety
    # margin. The full camera/frame/ray test subsequently verifies this bound.
    available=c['slot_height']/2-pin-c.get('pin_aperture_safety_margin',.015)
    half=math.asin(available/radius)
    states=[(int(d)+t)*2*math.pi/10 for d,t in zip(c['digit_sequence'],c['transition_progress'])]
    candidates=[]
    for count in range(10,101,10):
        pitch=2*math.pi/count
        for fraction in (0,.5):
            phase=fraction*pitch;counts=[];spreads=[]
            for state in states:
                angles=[(j*pitch+phase-state+math.pi)%(2*math.pi)-math.pi for j in range(count)]
                interior=sorted(a for a in angles if abs(a)<half)
                # Do not accept additional partly visible protrusions at the
                # aperture boundary, even if complete-pin count matches.
                partial=[a for a in angles if abs(a)<math.pi/2 and abs(radius*math.sin(a))-pin<c['slot_height']/2]
                counts.append((len(interior),len(partial)))
                ys=[radius*math.sin(a) for a in interior]
                gaps=[b-a for a,b in zip(ys,ys[1:])]
                spreads.append(max(gaps)/min(gaps) if gaps else float('inf'))
            if all(a==target and b==target for a,b in counts) and max(spreads)<1.12:
                candidates.append((count,fraction,phase,max(spreads)))
    if not candidates:raise ValueError('No uniform full-wheel pin pitch meets visible count/spacing and edge margins')
    count,fraction,phase,spread=min(candidates,key=lambda x:(x[0],x[3]))
    return {'target_visible_pins':target,'total_pin_count':count,'pin_pitch_degrees':360/count,
            'pin_phase_offset_degrees':math.degrees(phase),'safe_front_half_angle_degrees':math.degrees(half),
            'aperture_front_angular_interval_degrees':[-math.degrees(math.asin((c['slot_height']/2)/radius)),math.degrees(math.asin((c['slot_height']/2)/radius))],
            'predicted_max_spacing_ratio':spread,'method':'Uniform circumferential candidates tested against physical aperture, pin radius, safety margin and all fixed wheel states; verified later by projection and camera rays.'}
