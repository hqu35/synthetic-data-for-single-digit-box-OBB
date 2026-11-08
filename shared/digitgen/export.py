import base64
import json
from pathlib import Path


def write_json(path, data):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def read_labels(path, resolution):
    width, height = resolution
    boxes = []
    for line in Path(path).read_text().splitlines():
        fields = line.split()
        if len(fields)!=9 or fields[0]!='0':
            raise ValueError(f'Malformed digit_slot label: {path}')
        values = [float(v) for v in fields[1:]]
        boxes.append([[values[i]*width, values[i+1]*height] for i in range(0,8,2)])
    return boxes


def export_labels(path, boxes, resolution):
    width, height = resolution
    lines = ['0 '+' '.join(f'{v:.10f}' for x,y in box for v in (x/width,y/height)) for box in boxes]
    Path(path).write_text('\n'.join(lines)+'\n')


def svg_overlay(image_path, label_path, output_path, resolution):
    """Self-contained overlay reads exact on-disk labels; no Pillow required in Blender."""
    width, height = resolution
    boxes = read_labels(label_path, resolution)
    encoded = base64.b64encode(Path(image_path).read_bytes()).decode('ascii')
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             f'<image width="{width}" height="{height}" href="data:image/png;base64,{encoded}"/>']
    for i, box in enumerate(boxes):
        points = ' '.join(f'{x:.6f},{y:.6f}' for x,y in box)
        parts.append(f'<polygon points="{points}" fill="none" stroke="#35ff78" stroke-width="1.5"/>')
        x,y = box[0]
        parts.append(f'<circle cx="{x}" cy="{y}" r="2.5" fill="#ffba35"/><text x="{x+3}" y="{y-3}" fill="#00ff70" font-size="11">{i}</text>')
    parts.append('</svg>')
    Path(output_path).write_text('\n'.join(parts))
