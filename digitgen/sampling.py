"""Independent reproducible streams for mechanical, material, light and camera groups."""
import math
import random
from .assets import texture_spec


def weighted(rng,weights):
    return rng.choices(list(weights),list(weights.values()),k=1)[0]


def wheel_state(index,digit,transition_progress):
    if digit not in range(10) or not 0<=transition_progress<1:
        raise ValueError('Invalid wheel state')
    return {'index':index,'digit':digit,'next_digit':(digit+1)%10,'transition_progress':transition_progress,
            'transition':transition_progress>0,'wheel_rotation':(digit+transition_progress)*2*math.pi/10,
            'rotation_axis':'local +X','rotation_sign':1,'phi0_rad':0}


def sample_parameters(c,index,attempt=0):
    seed=c['seed']+index*100003+attempt*1000000007
    names=['geometry','wheel_states','materials','lighting','camera_pose','camera_appearance']
    seeds={name:(seed if c['randomization'][name] else c['randomization']['fixed_seed'])+j*104729 for j,name in enumerate(names)}
    rngs={name:random.Random(value) for name,value in seeds.items()}
    rng=rngs['camera_pose']; rot=c['rotation']
    pair_rng=random.Random(c['seed']+(index//2)*7919)
    sign=pair_rng.choice([-1,1])*(1 if index%2==0 else -1)
    t=rng.random()
    if rot['distribution']=='stratified':t=((index//2)+t)/((c['count']+1)//2)
    angle=sign*(rot['min_deg']+t*(rot['max_deg']-rot['min_deg']))
    if not c['randomization']['camera_pose']:angle=(rot['min_deg']+rot['max_deg'])/2
    cp=c['camera']
    camera={'projection':weighted(rng,cp['projection_weights']), 'distance':rng.uniform(*cp['distance']),
            'yaw_deg':rng.uniform(*cp['yaw_deg']),'pitch_deg':rng.uniform(*cp['pitch_deg']),'fov_deg':cp['fov_deg']}
    rng=rngs['geometry'];g=c['geometry'];pins=c['pins']
    n=int(weighted(rng,c['digit_counts']))
    radius=rng.uniform(*g['wheel_radius']);body=rng.uniform(*g['wheel_width'])
    ratio=rng.uniform(*g['gap_ratio']);rim=rng.uniform(*g['rim_width']);clearance=rng.uniform(*g['wheel_axial_clearance'])
    pin_length=rng.uniform(*pins['pin_length_ratio'])*body if pins['pins_enabled'] else 0
    assembly=body+rim+pin_length
    pitch=assembly+clearance
    w=pitch/(1+ratio) if g['slot_width'] is None else rng.uniform(*g['slot_width'])
    # Explicit slot-width overrides determine pitch; reject impossible physical layouts.
    pitch=w*(1+ratio)
    if pitch<assembly+clearance-1e-10 or w>=body:
        raise ValueError('Physical wheel/rim/pin envelope does not fit slot pitch or cover aperture')
    density=rng.choice(pins['pins_per_digit_interval'])
    mechanics={'wheel_axial_clearance':pitch-assembly,'assembly_width':assembly,
               'wheel_bevel_width':g['wheel_bevel_width'],'rim_width':rim,'rim_radius':radius*g['rim_radius_ratio'],
               'axle_radius':radius*g['axle_radius_ratio'],'radial_segments':g['radial_segments'],
               'pins_enabled':pins['pins_enabled'],'pins_per_digit_interval':density,
               'pin_count':density*10 if pins['pins_enabled'] else 0,
               'pin_radius':rng.uniform(*pins['pin_radius_ratio'])*radius,
               'pin_length':pin_length,'pin_radial_position':radius*pins['pin_radial_position'],
               'pin_bevel_width':pins['pin_bevel_width']}
    if mechanics['pin_radial_position']+mechanics['pin_radius']>mechanics['rim_radius']:
        raise ValueError('Pins extend beyond mounting rim')
    if mechanics['pin_count'] and 2*mechanics['pin_radius']>=2*mechanics['pin_radial_position']*math.sin(math.pi/mechanics['pin_count']):
        raise ValueError('Adjacent side pins overlap')
    rng=rngs['wheel_states']; wc=c['wheels'];states=[]
    for i in range(n):
        digit=rng.randrange(10)
        progress=rng.uniform(wc['transition_progress_min'],wc['transition_progress_max']) if rng.random()<wc['transition_probability'] else 0
        states.append(wheel_state(i,digit,progress))
    rng=rngs['materials'];a=c['appearance'];tint=rng.uniform(*a['cream_variation'])
    darkness=rng.uniform(*a['ink_darkness'])
    appearance={'material_preset':a['material_preset'],'material_color':[min(.98,x*tint) for x in a['material_color']],
                'roughness_range':list(a['roughness_range']),'micro_bump_strength':rng.uniform(*a['micro_bump_strength']),
                'micro_bump_distance':a['micro_bump_distance'],'aging_intensity':rng.uniform(*a['aging_intensity']),
                'color_variation':rng.uniform(*a['color_variation']),'ink_color':[darkness]*3,'ink_roughness':a['ink_roughness']}
    rng=rngs['lighting'];lighting={k:rng.uniform(*value) for k,value in c['lighting'].items()}
    rng=rngs['camera_appearance'];photo=c['camera_appearance'];preset=photo['preset']
    if preset=='randomized':preset=weighted(rng,photo['preset_weights'])
    strength=rng.uniform(*photo['cast_strength'])
    target={'neutral':[1,1,1],'cool_blue':[.82,.96,1.18],'warm':[1.12,1.01,.86]}[preset]
    photograph={'preset':preset,'postprocess_color_cast':[1+strength*(x-1) for x in target],
                'camera_white_balance':[rng.uniform(*photo['white_balance_variation']) for _ in range(3)],
                'camera_exposure':rng.uniform(*photo['exposure_stops']),'contrast':rng.uniform(*photo['contrast']),
                'blur_sigma_px':rng.uniform(*photo['blur_sigma_px']),'sensor_noise_std':rng.uniform(*photo['sensor_noise_std']),
                'noise_seed':seeds['camera_appearance']%4294967295,
                'defocus_enabled':photo['defocus_enabled'],'defocus_fstop':rng.uniform(*photo['defocus_fstop']),
                'processing_space':'display-referred AgX sRGB PNG decoded to linear RGB; gain/exposure/contrast/noise, Gaussian softness, clip then sRGB encode',
                'geometry_transform':'identity'}
    return {'index':index,'attempt':attempt,'seed':seed,'group_seeds':seeds,'digit_count':n,
            'digit_sequence':''.join(str(s['digit']) for s in states),'wheels':states,'requested_angle_deg':angle,
            'slot_width':w,'wheel_width':body,'wheel_radius':radius,'slot_height':radius*2*math.pi/10*g['slot_height_step_ratio'],
            'gap_ratio':ratio,'gap':w*ratio,'pitch':pitch,'mechanics':mechanics,'camera':camera,
            'appearance':appearance,'lighting':lighting,'photograph':photograph,'texture':texture_spec(c)}
