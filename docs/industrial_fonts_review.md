# Industrial typography review — Task A

The existing fixed `00054` mechanical scene now supports two review candidates: `din1451_like` (D-DIN Regular) and `ocr_b` (OCR-B outline `ocrb10`). An optional `din_condensed_like` candidate is also included. These are exploratory candidates, not confirmed manufacturer fonts.

## Review artifacts

| Candidate | Fixed scene | Upright 0–9 sheet |
|---|---|---|
| D-DIN Regular | [00054](../outputs/industrial_fonts_review/din1451_like_00054.png) | [Sheet](../outputs/industrial_fonts_review/din1451_like_upright_0-9.png) |
| OCR-B outline | [00054](../outputs/industrial_fonts_review/ocr_b_00054.png) | [Sheet](../outputs/industrial_fonts_review/ocr_b_upright_0-9.png) |
| D-DIN Condensed, supplementary | [00054](../outputs/industrial_fonts_review/din_condensed_like_00054.png) | [Sheet](../outputs/industrial_fonts_review/din_condensed_like_upright_0-9.png) |

Each candidate has a packed `.blend`, full resolved JSON configuration, original cylindrical mask, and atlas manifest in the results directory. The upright sheet undoes the cylinder UV transpose, so the 0–9 lettering can be inspected directly. The cylindrical mask deliberately has a different orientation for the established UV mapping.

## Font provenance and licensing

**DIN candidate:** D-DIN is an openly distributed DIN 1451-derived family commissioned by Datto from Monotype. It is a substitution for exact DIN 1451, not a claim of exact standards compliance. D-DIN Condensed is the narrow supporting candidate, not a certified DIN Engschrift implementation. Original font binaries are unchanged. The [original project README](https://github.com/amcchord/datto-d-din/blob/main/README.md) and [copyright/license notice](https://github.com/amcchord/datto-d-din/blob/main/COPYING.txt) identify the SIL Open Font License 1.1 and reserved font names. Files were downloaded from pinned commit `e199c8441e758d6e492cd01ef52c3c67ba4bae26`. `COPYING.txt`, `OFL-1.1.txt`, `FONTLOG.txt`, and original README are retained beside the binaries under `assets/fonts/industrial/`.

**OCR-B candidate:** The [CTAN OCR-B outline package](https://ctan.org/pkg/ocr-b-outline) supplies `ocrb10.otf`, converted by Zdeněk Wagner from Norbert Schwarz's METAFONT implementation. Its [upstream README](https://ctan.org/tex-archive/fonts/ocr-b-outline) explicitly allows free use, modification and distribution without limitation; that complete notice is retained as `OCR-B-README.txt`. This is an actual open OCR-B implementation, not Microsoft's separately licensed OCRB. Upstream warns that automatic outline conversion was not carefully examined and large-size results may be unsuitable; our ten-digit sheets and native renders are supplied for visual review. No OCR compliance certification is claimed. The downloaded CTAN archive and each retained font file are SHA-256 recorded in `assets/fonts/industrial/source_manifest.json`.

## What remains fixed

Only the texture image reference changes between comparisons. Every wheel uses one complete atlas with the same font across all ten digits. The comparison script asserts exact equality of mesh vertex/polygon hashes, mesh transforms and visibility, active camera matrix/lens, lights, world shader inputs, resolution, and material shader connections before and after font replacement. The source is the already reviewed `final_stage1_review.blend`; it is never overwritten.

The original ten equal 36° intervals, 0–9 order, wheel pose `00054` with final-wheel progress 0.05, band width, pin geometry, aperture mapping, shader separation and glyph fill/alignment settings are preserved. Maximum glyph width and height retain the existing atlas generator's normalization: the Condensed font does not shrink cell width or band geometry. Natural relative numeral widths and stroke shapes vary with the font.

**Deferred:** excess circumferential blank space and the rolling-transition midpoint issue remain unresolved. This task intentionally does not recalibrate spacing, pitch, aperture or roll semantics.

## Reproduce

From the source workspace:

```bash
python3 prepare_font_review.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python industrial_fonts_review.py
python3 -m unittest discover -s tests -v
```

The isolated scripts produce only deterministic typography inspection artifacts. Native renders use the saved Cycles scene's 64 samples, denoising and seed 0. CPU execution uses four threads. The accompanying `inspection_report.json` records scene invariants and each resolved configuration.

The inherited generic-generator configs `configs/font_din1451_like.json`, `configs/font_ocr_b.json`, and `configs/font_din_condensed_like.json` select these presets without changing the base preview parameters. They were validated and their atlases prepared; no dataset generation was run. The supplied mechanical comparison images continue to use the approved Stage 1 scene, not a newly sampled generic-generator scene.

For normal generator configs, select `--font-preset din1451_like`, `--font-preset ocr_b`, or `--font-preset din_condensed_like` with `prepare_assets.py`, and use the same `font_preset` in the renderer's configuration. `font_candidates.resolve_config` resolves a full consistent typography dictionary. `digitgen.assets.texture_spec` uses the identical resolver, so its hash matches preparation. Legacy configs without a preset retain their previous atlas hash and font identity.

## Validation boundary and stop

The 20 existing project tests passed. `atlas_validation.json` confirms all ten glyphs are distinct and nonempty, per-font family identities and font/atlas hashes, unchanged cell fill parameters, and the unchanged legacy Barlow atlas hash. `inspection_report.json` records the actual Blender version, source scene checksum and frozen-scene assertions. The delivered images were visually inspected for upright numerals, legibility and consistent framing.

These are inspection outputs only. No datasets, diffusion, model training, production rendering or spacing changes were added. Stop for human typography review; Task B independently uses the stable Barlow atlas.
