"""Read-only Stage 1 artifact audit plus inspection contact/comparison sheets."""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageStat


def review(out):
    out=Path(out);report=json.loads((out/'inspection_report.json').read_text())
    if report['training_dataset_generated'] is not False:raise ValueError('Not a geometry-only inspection')
    check=report['geometry_checks']
    if check['status']!='passed' or check['wheel_count']!=5 or check['total_pins']!=100:
        raise ValueError('Mechanical sanity checks did not pass')
    for folder in ('images','labels','metadata'):
        if (out/folder).exists():raise ValueError('Unexpected training-export directories in Stage 1 output')
    if report['parameters']['digit_sequence']!='00054':raise ValueError('Fixed reading changed')
    if [w['transition_progress'] for w in report['parameters']['wheels']]!=[0,0,0,0,.05]:raise ValueError('Fixed transition changed')
    views=report['views'];required=['A_three_quarter_neutral','B_right_pin_closeup','C_front_neutral',
                                  'D_grazing_curvature','E_three_quarter_cool_blue','F_front_cool_blue']
    if not all(name in views for name in required):raise ValueError('Missing required views')
    thumbnails=[];decoded=[]
    for name,view in views.items():
        with Image.open(out/view['file']) as im:
            im.load()
            if im.format!='PNG' or list(im.size)!=view['resolution']:raise ValueError('Inspection image dimensions/format mismatch')
            if max(ImageStat.Stat(im.convert('RGB')).stddev)<8:raise ValueError('Inspection image lacks visible contrast')
            thumb=im.convert('RGB');thumb.thumbnail((480,310))
        tile=Image.new('RGB',(480,340),(22,25,30));tile.paste(thumb,((480-thumb.width)//2,(310-thumb.height)//2))
        ImageDraw.Draw(tile).text((8,318),name,fill='white');thumbnails.append(tile);decoded.append(name)
    for neutral,cool,target in [('A_three_quarter_neutral','E_three_quarter_cool_blue','neutral_vs_blue_assembly.png'),
                                ('C_front_neutral','F_front_cool_blue','neutral_vs_blue_front.png')]:
        a,b=views[neutral],views[cool]
        if a['camera_matrix_world']!=b['camera_matrix_world'] or a['camera_lens_mm']!=b['camera_lens_mm']:
            raise ValueError('Comparison camera differs')
        if a['material_color']!=b['material_color']:raise ValueError('Blue comparison recolored the material')
        for la,lb in zip(a['lights'],b['lights']):
            if any(la[key]!=lb[key] for key in ('position','energy','size')):raise ValueError('Comparison changed more than illumination color')
        with Image.open(out/a['file']) as first,Image.open(out/b['file']) as second:
            pair=Image.new('RGB',(first.width*2,first.height+28),(22,25,30))
            pair.paste(first,(0,0));pair.paste(second,(first.width,0))
            draw=ImageDraw.Draw(pair);draw.text((10,first.height+7),'Neutral illumination',fill='white')
            draw.text((first.width+10,first.height+7),'Cool illumination; identical cream material and camera',fill='white')
            pair.save(out/target)
    cols=2;rows=(len(thumbnails)+1)//2
    sheet=Image.new('RGB',(cols*480,rows*340),(22,25,30))
    for i,tile in enumerate(thumbnails):sheet.paste(tile,((i%cols)*480,(i//cols)*340))
    sheet.save(out/'inspection_contact_sheet.png')
    summary={'status':'passed_saved_inspection_audit','stage':'Stage 1 only; human approval pending',
             'images_decoded':decoded,'fixed_wheels':5,'total_pins':100,
             'geometry_checks':'passed','paired_camera_and_material_invariance':'passed',
             'training_data_generated':False,
             'visual_review':'Contact sheets still require human geometry approval.'}
    (out/'artifact_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path)
    review(parser.parse_args().output)
