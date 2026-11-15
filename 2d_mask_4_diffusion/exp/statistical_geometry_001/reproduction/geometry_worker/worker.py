"""Deterministic statistical sampling and reconstructible 2D strip geometry."""
import copy,hashlib,json,math
from pathlib import Path
import numpy as np
from .geometry import boundary,min_area_rect,validate_strip

DEFAULT_CONFIG=Path(__file__).with_name('config.json')


def project(H,xy):
    v=H@np.array([xy[0],xy[1],1.]);
    if v[2]<=.2:raise ValueError('Invalid projective depth')
    return v[:2]/v[2]


def jacobian(H,xy):
    den=(H@np.array([*xy,1.]))[2];p=project(H,xy)
    return (H[:2,:2]-np.outer(p,H[2,:2]))/den


def random_parameters(rng,c):
    pick=lambda name:float(rng.uniform(*c[name]))
    w=pick('strip_width_fraction');h=pick('strip_height_fraction');gap=pick('gap_to_width_ratio')
    roll=pick('global_roll_deg');qx=pick('horizontal_perspective');qy=pick('vertical_perspective');sx=pick('horizontal_foreshortening');sy=pick('vertical_scale')
    slant=pick('shared_slant_halfwidth');bend=pick('shared_curvature_halfwidth')
    angle=math.radians(roll);co,si=math.cos(angle),math.sin(angle);ratio=c['height']/c['width']
    # Rotation is applied in pixel metric despite normalized x/y coordinates.
    R=np.array([[co,-si*ratio,0],[si/ratio,co,0],[0,0,1.]])
    S=np.diag([sx,sy,1]);P=np.array([[1.,0,0],[0,1.,0],[qx,qy,1.]])
    T=np.array([[1.,0,.5],[0,1.,.5],[0,0,1.]])
    H=T@P@R@S@np.array([[1.,0,-.5],[0,1.,-.5],[0,0,1.]])
    return {'strip_width_fraction':w,'strip_height_fraction':h,'gap_to_width_ratio':gap,
            'global_roll_deg':roll,'horizontal_perspective':qx,'vertical_perspective':qy,
            'horizontal_foreshortening':sx,'vertical_scale':sy,'shared_slant_halfwidth':slant,
            'shared_curvature_halfwidth':bend,'homography':H.tolist()}


def sample(seed,reading,c):
    if len(reading)!=5 or not reading.isascii() or not reading.isdigit():raise ValueError('Reading must contain exactly five ASCII digits')
    width,height=int(c['width']),int(c['height']);n=int(c['boundary_samples_per_edge'])
    if width<64 or height<64 or n<16 or n>1024:raise ValueError('Invalid canvas or contour sampling resolution')
    rng=np.random.default_rng(seed);D=np.diag([width,height])
    for attempt in range(int(c['max_attempts'])):
        try:
            p=random_parameters(rng,c);H=np.asarray(p['homography']);w=p['strip_width_fraction'];h=p['strip_height_fraction'];pitch=w*(1+p['gap_to_width_ratio'])
            background=int(rng.integers(c['background_gray'][0],c['background_gray'][1]+1));gray=int(rng.integers(c['strip_gray'][0],c['strip_gray'][1]+1));strips=[]
            axis=D@jacobian(H,[.5,.5])[:,0];axis/=np.linalg.norm(axis)
            for i in range(5):
                center=[.5+(i-2)*pitch,.5];J=jacobian(H,center);point=D@project(H,center)
                wf=1+float(rng.uniform(*c['local_width_deviation']));hf=1+float(rng.uniform(*c['local_height_deviation']))
                local_bend=p['shared_curvature_halfwidth']+float(rng.uniform(*c['local_curvature_deviation']))
                a=D@J[:,0]*(w/2)*wf;b=D@J[:,1]*(h/2)*hf + a*p['shared_slant_halfwidth']
                k=a*local_bend
                coeff={'p':point.tolist(),'a':a.tolist(),'b':b.tolist(),'k':k.tolist()}
                contour=boundary(coeff,n);box,area=min_area_rect(contour);det=validate_strip(coeff,contour,box,width,height)
                delta=int(rng.integers(c['local_gray_delta'][0],c['local_gray_delta'][1]+1));color=max(0,min(255,gray+delta))
                strips.append({'index':i,'digit':reading[i],'coefficients_px':coeff,'fill_gray':color,'contour_px':contour.tolist(),
                  'contour_normalized':(contour/[width,height]).tolist(),'obb_px':box.tolist(),
                  'obb_normalized':(box/[width,height]).tolist(),'obb_area_px2':area,'jacobian_endpoint_determinants':det,
                  'local_width_multiplier':wf,'local_height_multiplier':hf,'local_curvature_halfwidth':local_bend,
                  'quadratic_side_max_chord_error_px':float(np.linalg.norm(k)/(n*n))})
            # Require a separating line between each pair in the common assembly axis.
            intervals=[(np.min(np.asarray(x['contour_px'])@axis),np.max(np.asarray(x['contour_px'])@axis)) for x in strips]
            gaps=[float(intervals[i+1][0]-intervals[i][1]) for i in range(4)]
            if any(g<=1 for g in gaps):raise ValueError('Strips overlap or have no positive separation')
            return {'schema_version':1,'seed':int(seed),'reading':reading,'resolution':[width,height],
                    'boundary_samples_per_edge':n,'background_gray':background,'shared_parameters':p,
                    'sampling_configuration':copy.deepcopy(c),'attempt':attempt,'separation_axis_px':axis.tolist(),
                    'minimum_separation_gaps_px':gaps,'strips':strips,
                    'geometry_definition':'F_i(s,t)=p_i+a_i*s+b_i*t+k_i*t^2 in pixels; s,t in [-1,1].',
                    'annotation_definition':'Minimum-area rectangle of the sampled boundary polygon in pixel metric; class 0 denotes a strip.',
                    'sampling_status':'provisional, not empirically calibrated'}
        except ValueError:
            continue
    raise RuntimeError(f'Could not sample a valid assembly in {c["max_attempts"]} attempts for seed {seed}')


def reconstruct(data):
    n=data['boundary_samples_per_edge'];width,height=data['resolution'];result=copy.deepcopy(data)
    for strip in result['strips']:
        contour=boundary(strip['coefficients_px'],n);box,area=min_area_rect(contour);det=validate_strip(strip['coefficients_px'],contour,box,width,height)
        strip.update(contour_px=contour.tolist(),contour_normalized=(contour/[width,height]).tolist(),obb_px=box.tolist(),obb_normalized=(box/[width,height]).tolist(),obb_area_px2=area,jacobian_endpoint_determinants=det)
    return result


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
