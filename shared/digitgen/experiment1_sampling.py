"""Host-testable deterministic parameters for the approved controlled experiment."""
import math
import random


def temperature_rgb(kelvin):
    """Restrained Kelvin-inspired light tint; actual RGB is always recorded.

    This intentionally simple tint control is not a calibrated spectral model.
    """
    if kelvin<=6500:
        return [1.0, .96+.04*(kelvin-5700)/800, .88+.12*(kelvin-5700)/800]
    t=min(1,(kelvin-6500)/2000)
    return [1-.24*t,1-.09*t,1.0]


def sample_parameters(config,index,attempt=0):
    if not 1<=index<=config['count'] or not 0<=attempt<config['validation']['max_attempts_per_sample']:
        raise ValueError('Sample or attempt outside the configured bounded experiment')
    seed=config['seed']+index*1009+attempt*1000003;rng=random.Random(seed)
    def interval(group,key):return rng.uniform(*config[group][key])
    cool=index%2==0
    temperature=interval('lighting','cool_temperature_kelvin' if cool else 'neutral_temperature_kelvin')
    result={'sample_id':f'{index:06d}','index':index,'attempt':attempt,'seed':seed,
        'camera':{key:interval('camera',key) for key in ['yaw_deg','pitch_deg','roll_deg','distance','focal_length_mm']},
        'register':{key:interval('register',key) for key in ['rotation_x_deg','rotation_y_deg','rotation_z_deg']},
        'lighting':{'preset':'cool_blue' if cool else 'neutral','temperature_kelvin':temperature,
            'temperature_rgb':temperature_rgb(temperature),'intensity_scale':interval('lighting','intensity_scale'),
            'world_strength':interval('lighting','world_strength'),
            'light_seed':rng.randrange(2147483647)},
        'appearance':{'exposure_ev':interval('appearance','exposure_ev'),'contrast':interval('appearance','contrast'),
            'substrate_color_scale':interval('appearance','substrate_color_scale'),
            'substrate_rgb_gain':[interval('appearance','substrate_rgb_gain') for _ in range(3)],
            'sensor_noise_std':interval('appearance','sensor_noise_linear_rgb_std') if rng.random()<config['appearance']['sensor_noise_probability'] else 0,
            'noise_seed':rng.randrange(2147483647)}}
    if config['camera'].get('auto_fit_register'):
        result['camera']['target_register_area_fraction']=interval('camera','register_image_area_fraction')
    poses=config['camera'].get('pose_overrides')
    if poses:
        if len(poses)!=config['count']:raise ValueError('Provide one review camera pose per sample')
        result['camera'].update(poses[index-1])
    return result
