"""Audit saved glass review artifacts and build review sheets; never change labels."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent


def sheet(folder, name, entries):
    rows = []
    for stem, title in entries:
        im = Image.open(folder / f'{stem}.png').convert('RGB')
        im.thumbnail((1200, 525))
        row = Image.new('RGB', (1240, im.height + 55), '#eeeeee')
        ImageDraw.Draw(row).text((20, 12), title, fill='black')
        row.paste(im, ((1240-im.width)//2, 42))
        rows.append(row)
    result = Image.new('RGB', (1240, sum(r.height for r in rows)), '#eeeeee')
    y = 0
    for row in rows:
        result.paste(row, (0, y)); y += row.height
    result.save(folder / name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='outputs/glass_review')
    args = parser.parse_args(); folder = ROOT / args.output
    report = json.loads((folder/'inspection_report.json').read_text())
    views = report['views']; assert len(views) == 7
    c = report['config']; d = report['glass_dimensions']
    assert report['mechanical_geometry_unchanged'] and report['oblique_tolerance_passed']
    assert d['closed_mesh'] == 'passed' and d['signed_volume'] > 0
    assert d['one_continuous_cover'] and d['air_gap_to_mechanics'] > 0
    assert d['back_z'] > d['highest_mechanical_surface_z']
    implementation = hashlib.sha256((ROOT/'digitgen/glass.py').read_bytes()+(ROOT/'glass_review.py').read_bytes()).hexdigest()
    assert implementation == report['source_glass_implementation_sha256']
    base = views['01_no_glass_baseline']; neutral = views['02_glass_neutral']
    assert base['lights'] == neutral['lights']
    label_checks = {}
    for name, view in views.items():
        assert view['mechanical_signature'] == report['mechanical_signature']
        assert view['seed'] == c['seed'] and not view['sensor_noise']['enabled']
        im = Image.open(folder/f'{name}.png'); assert im.size == tuple(view['resolution']) and im.format == 'PNG'
        assert json.loads((folder/f'{name}_parameters.json').read_text()) == view
        if name != '04_glass_oblique':
            assert view['camera_world_matrix'] == base['camera_world_matrix']
        if name not in ('03_glass_cool_blue', '04_glass_oblique'):
            assert view['lights'] == base['lights']
        mat = view['glass_material']
        assert mat['alpha'] == 1 and mat['metallic'] == 0 and mat['ior'] == 1.5 and mat['transmission_weight'] == 1
        rows = [list(map(float, line.split())) for line in (folder/f'{name}_slot_obbs.txt').read_text().splitlines()]
        assert len(rows) == 5 and all(len(row) == 9 and row[0] == 0 for row in rows)
        points = np.asarray([np.asarray(row[1:]).reshape(4,2)*view['resolution'] for row in rows])
        assert np.isfinite(points).all() and (points >= 0).all() and (points <= view['resolution']).all()
        optical = report['oblique_optical_check'] if name == '04_glass_oblique' else report['front_optical_check']
        error = float(np.max(np.abs(points-np.asarray([r['original_obb_px'] for r in optical]))))
        assert error < .002, error
        assert all(r['all_optical_paths_inside_single_cover'] for r in optical)
        label_checks[name] = {'label_count': 5, 'max_export_roundtrip_error_px': error}
        if name in ('02_glass_neutral', '04_glass_oblique'):
            overlay = im.convert('RGB'); draw = ImageDraw.Draw(overlay)
            for i, polygon in enumerate(points):
                xy = [tuple(p) for p in polygon]
                draw.line(xy+[xy[0]], fill='#00ff66', width=2)
                draw.text((min(p[0] for p in xy)+5,min(p[1] for p in xy)+5), f'slot {i}', fill='#00ff66')
                apparent = [tuple(p) for p in optical[i]['apparent_refracted_obb_px']]
                draw.line(apparent+[apparent[0]], fill='#ff7755', width=1)
            overlay.save(folder/f'{name}_obb_inspection.png')
    # Image-space cross-check using gradients inside each slot, away from the highlights.
    images = [np.asarray(Image.open(folder/f'{s}.png').convert('L'), dtype=float) for s in ('01_no_glass_baseline','02_glass_neutral')]
    gradients = [np.hypot(*np.gradient(im)) for im in images]
    estimates = []
    for r in report['front_optical_check']:
        box = np.asarray(r['original_obb_px']); x0,y0 = np.ceil(box.min(axis=0)+18).astype(int); x1,y1 = np.floor(box.max(axis=0)-18).astype(int)
        y0 += 35
        a = gradients[0][y0:y1,x0:x1]; a = (a-a.mean())/(a.std()+1e-9)
        scores = []
        for dy in range(-4,5):
            for dx in range(-4,5):
                b = gradients[1][y0+dy:y1+dy,x0+dx:x1+dx]; b = (b-b.mean())/(b.std()+1e-9)
                scores.append((float(np.mean(a*b)), dx, dy))
        score,dx,dy = max(scores)
        estimates.append({'wheel': r['wheel'], 'best_integer_translation_px':[dx,dy], 'gradient_correlation':score})
    sheet(folder, 'glass_comparison.png', [('01_no_glass_baseline','No glass / identical camera and lights'),('02_glass_neutral','Neutral glass / IOR 1.50 / roughness 0.035'),('03_glass_cool_blue','Cool-blue lighting / same physical cover'),('04_glass_oblique','Oblique / physical edge thickness and pose-dependent reflections')])
    sheet(folder, 'roughness_comparison.png', [('05_roughness_0015','Roughness 0.015'),('02_glass_neutral','Roughness 0.035'),('06_roughness_0070','Roughness 0.070')])
    sheet(folder, 'microstructure_comparison.png', [('02_glass_neutral','Clean glass / microstructure disabled'),('07_subtle_microstructure','Subtle correlated microstructure enabled / sensor noise disabled')])
    result = {'status':'passed','mechanical_geometry_unchanged':True,'source_implementation_hash_matches':True,'saved_labels_unchanged':label_checks,
              'front_max_ideal_boundary_shift_px':max(r['max_boundary_shift_px'] for r in report['front_optical_check']),
              'oblique_max_ideal_boundary_shift_px':max(r['max_boundary_shift_px'] for r in report['oblique_optical_check']),
              'oblique_max_shift_fraction_slot_width':max(r['shift_fraction_of_slot_width'] for r in report['oblique_optical_check']),
              'front_image_gradient_translation_estimates':estimates,
              'limits':'Gradient translation is an integer-pixel image cross-check, not subpixel ground truth. Snell diagnostics assume a planar parallel slab and exclude bevel and micro-normal perturbations. Oblique labels remain original projections; inspect the overlay before reuse in a dataset.'}
    (folder/'artifact_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
