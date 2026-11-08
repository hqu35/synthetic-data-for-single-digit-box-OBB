"""Open industrial-font candidates; resolve before atlas hashing or rendering.

Presets replace only font identity and provenance, preserving the caller's cell
size, glyph fill ratios, alignment, UV mapping and wheel rotation semantics.
"""
from copy import deepcopy

PRESETS = {
    'din1451_like': {
        'font': 'assets/fonts/industrial/D-DIN.ttf',
        'font_family': 'D-DIN', 'font_weight': 'Regular',
        'font_license': 'assets/fonts/industrial/COPYING.txt',
        'description': 'D-DIN Regular: open DIN 1451-derived candidate; not an exact manufacturer match.',
    },
    'din_condensed_like': {
        'font': 'assets/fonts/industrial/D-DINCondensed.ttf',
        'font_family': 'D-DIN Condensed', 'font_weight': 'Regular',
        'font_license': 'assets/fonts/industrial/COPYING.txt',
        'description': 'D-DIN Condensed: optional narrow industrial candidate, not certified DIN Engschrift.',
    },
    'ocr_b': {
        'font': 'assets/fonts/industrial/ocrb10.otf',
        'font_family': 'ocrb10', 'font_weight': 'Regular',
        'font_license': 'assets/fonts/industrial/OCR-B-README.txt',
        'description': 'OCR-B outline ocrb10 by Zdenek Wagner from Norbert Schwarz METAFONT sources; not Microsoft OCRB.',
    },
}


def resolve_typography(typography, preset):
    if preset not in PRESETS:
        raise ValueError(f'Unknown font preset {preset!r}; choose from {list(PRESETS)}')
    resolved = deepcopy(typography)
    resolved.update({k: v for k, v in PRESETS[preset].items() if k != 'description'})
    return resolved


def resolve_config(config, preset=None):
    resolved = deepcopy(config)
    name = preset or resolved.get('font_preset')
    if name:
        resolved['typography'] = resolve_typography(resolved['typography'], name)
        resolved['font_preset'] = name
    return resolved
