"""Deterministic dimensions for Stage 1's raised-band mechanical review."""
def raised_layout(c):
    if 'slot_width_fixed' in c:
        slot=c['slot_width_fixed'];band=slot*c['band_to_slot_ratio']
    else:
        band=c['old_band_width']*c['band_width_scale']
        slot=band/c['band_to_slot_ratio']
    remainder=slot-band;left=remainder*c['left_margin_share'];right=remainder-left
    band_left=-slot/2+left;band_right=band_left+band
    root=band_right+c['edge_rim_width'];tip=root+c['pin_length']
    pitch=slot*(1+c['digit_gap_ratio'])
    minimum=min(-c['base_width']/2,band_left);maximum=max(c['base_width']/2,tip)
    clearance=pitch-(maximum-minimum)
    if not 0<c['base_radius']<c['band_radius']:
        raise ValueError('Raised band radius must exceed base drum radius')
    if not 0<band<c['base_width'] or not 0<c['band_to_slot_ratio']<1:
        raise ValueError('The base must be wider than its raised numeral band')
    if band_left<-c['base_width']/2 or band_right>c['base_width']/2:
        raise ValueError('Band is not supported by the underlying drum')
    if tip>slot/2 or root<band_right:
        raise ValueError('Band-edge pin extension exceeds the right slot region')
    if c['pin_radial_position']-c['pin_radius']<=c['base_radius']:
        raise ValueError('Pin shafts intersect the recessed base drum')
    if c['pin_radial_position']+c['pin_radius']>c['edge_rim_radius']:
        raise ValueError('Pin roots must be supported by the annular edge rim')
    if clearance<c['minimum_clearance']:
        raise ValueError('Adjacent complete assemblies intersect or lack clearance')
    if 'target_visible_pins' in c:
        if c['target_visible_pins'] not in (3,4):raise ValueError('Visible pin target must be 3 or 4')
    elif 'total_pin_count' not in c and c['pins_per_digit_interval'] not in (2,3):raise ValueError('Pin density must be 2 or 3')
    return {'base_radius':c['base_radius'],'band_radius':c['band_radius'],
            'radial_raise':c['band_radius']-c['base_radius'],'base_width':c['base_width'],
            'old_band_width':c['old_band_width'],'band_width_scale':band/c['old_band_width'],
            'band_width':band,'slot_width':slot,'band_to_slot_ratio':band/slot,
            'left_margin':left,'right_margin':right,'band_left':band_left,'band_right':band_right,
            'band_center':(band_left+band_right)/2,'pin_root_x':root,'pin_tip_x':tip,
            'pin_center_x':(root+tip)/2,'pin_radial_position':c['pin_radial_position'],
            'pin_radius':c['pin_radius'],'pin_length':c['pin_length'],
            'digit_gap_ratio':c['digit_gap_ratio'],'visible_gap':slot*c['digit_gap_ratio'],
            'pitch':pitch,'physical_width':maximum-minimum,'physical_clearance':clearance,
            'axial_min':minimum,'axial_max':maximum}
