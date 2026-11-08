import copy
import json
import math
from pathlib import Path


def merge(base, override):
    out = copy.deepcopy(base)
    for k, v in override.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def load_config(path, seen=None):
    path = Path(path).resolve()
    seen = set() if seen is None else seen
    if path in seen:
        raise ValueError("Circular config inheritance")
    seen.add(path)
    data = json.loads(path.read_text())
    parent = data.pop('extends', None)
    if parent:
        data = merge(load_config(path.parent / parent, seen), data)
    validate_config(data)
    return data


def validate_config(c):
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    def interval(value, name, positive=False):
        require(len(value)==2 and all(math.isfinite(x) for x in value) and value[0]<=value[1], f"Invalid {name} interval")
        if positive:
            require(value[0]>0, f"{name} must be positive")
    require(isinstance(c['count'], int) and c['count']>0, 'count must be a positive integer')
    require(isinstance(c['seed'], int), 'seed must be an integer')
    require(len(c['resolution'])==2 and all(isinstance(x,int) and x>=64 for x in c['resolution']), 'Invalid resolution')
    for key, allowed in [('digit_counts', {'5','6'}), ('camera.projection_weights', {'ORTHO','PERSP'})]:
        weights = c['digit_counts'] if key=='digit_counts' else c['camera']['projection_weights']
        require(bool(weights) and set(weights)<=allowed and all(math.isfinite(v) and v>=0 for v in weights.values()) and sum(weights.values())>0, f'Invalid {key}')
    r, g, cam = c['rotation'], c['geometry'], c['camera']
    require(0 < r['tolerance_deg'] < r['min_deg'] < r['max_deg'] < 40, 'Invalid nonzero rotation range/tolerance')
    require(r['max_spread_deg']>0, 'Angle spread must be positive')
    require(r['distribution'] in ('uniform','stratified'), 'Unknown angle distribution')
    for k in ('wheel_width','wheel_radius','gap_ratio','wheel_axial_clearance','rim_width'):
        interval(g[k], k, True)
    if g['slot_width'] is not None:
        interval(g['slot_width'],'slot_width',True)
    require(g['wheel_bevel_width']>0 and g['frame_depth']>0 and g['aperture_standoff']>g['frame_depth'], 'Invalid mechanical bevel/aperture depth')
    require(0<g['rim_radius_ratio']<=1 and 0<g['axle_radius_ratio']<.5, 'Invalid rim or axle radius')
    require(isinstance(g['radial_segments'],int) and g['radial_segments']>=64,'Insufficient cylinder radial resolution')
    require(0<g['slot_height_step_ratio']<=1 and g['frame_border']>0, 'Invalid aperture/frame geometry')
    require(g['slot_height_step_ratio']*2*math.pi/10 < 2, 'Aperture exceeds cylinder diameter')
    require(0<cam['margin_fraction']<0.4 and 5<cam['fov_deg']<100, 'Invalid camera framing')
    for k in ('distance','yaw_deg','pitch_deg'):
        interval(cam[k], k, k=='distance')
    require(max(abs(x) for x in cam['yaw_deg']+cam['pitch_deg'])<=10, 'Initial generator supports modest perspective only (<=10 degrees)')
    for k in ('transition_probability',):
        require(0<=c['wheels'][k]<=1, f'Invalid {k}')
    require(0<c['wheels']['transition_progress_min']<=c['wheels']['transition_progress_max']<1, 'Transitions must lie strictly between digits')
    require(c['annotation_target']=='viewing_aperture', 'Only viewing_aperture is implemented; glyph boxes require a separate target adapter')
    require(c['render']['engine']=='CYCLES' and c['render']['device']=='CPU', 'Portable implementation currently supports Cycles CPU')
    require(c['render']['samples']>=1 and c['render']['threads']>=1, 'Invalid render quality')
    require(c['max_attempts']>=1, 'max_attempts must be positive')
    a=c['appearance']
    require(a['material_preset'] in ('basic','reference_dark_plastic','meter_cream_matte'),'Unknown plastic preset')
    require(len(a['material_color'])==3 and all(0<x<=1 for x in a['material_color']),'Invalid material color')
    for k in ('cream_variation','roughness_range','micro_bump_strength','aging_intensity','color_variation','ink_darkness'):
        interval(a[k],k)
    require(0<=a['roughness_range'][0]<=a['roughness_range'][1]<=1 and a['micro_bump_distance']>0,'Invalid plastic response')
    pins=c['pins']
    require(bool(pins['pins_per_digit_interval']) and set(pins['pins_per_digit_interval'])<={2,3},'Pin density must be 2 or 3 per interval')
    for k in ('pin_radius_ratio','pin_length_ratio'):interval(pins[k],k,True)
    require(0<pins['pin_radial_position']<1 and pins['pin_bevel_width']>=0,'Invalid pin position/bevel')
    t=c['typography']
    require(0<t['numeral_height']<.95 and 0<t['numeral_width']<.95,'Numerals must leave a texture seam margin')
    require(t['segment_pixels']>=128 and t['axial_pixels']>=128,'Insufficient texture resolution')
    photo=c['camera_appearance']
    require(photo['preset'] in ('neutral','cool_blue','warm','randomized'),'Unknown camera appearance preset')
    require(set(photo['preset_weights'])<= {'neutral','cool_blue','warm'} and sum(photo['preset_weights'].values())>0 and all(v>=0 for v in photo['preset_weights'].values()),'Invalid camera preset weights')
    for k in ('cast_strength','white_balance_variation','exposure_stops','contrast','blur_sigma_px','sensor_noise_std','defocus_fstop'):interval(photo[k],k)
    require(photo['blur_sigma_px'][0]>=0 and photo['sensor_noise_std'][0]>=0,'Invalid optical effect')
    require(set(c['randomization'])=={'geometry','wheel_states','materials','lighting','camera_pose','camera_appearance','fixed_seed'},'Invalid randomization groups')
    for k, value in c['lighting'].items():
        interval(value, 'lighting.'+k, k not in ('key_x','key_y','fill_x','fill_y'))
