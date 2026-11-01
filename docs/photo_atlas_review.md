# User-supplied photographic numeral atlas

[All ten digits on the 3D register](../outputs/photo_atlas_adjusted/digits_contact_sheet.png) · [Rolling-gap comparison](../outputs/photo_atlas_adjusted/inspection_contact_sheet.png) · [Extracted numeral shapes](../outputs/photo_atlas_adjusted/extracted_numerals.png) · [Images](../outputs/photo_atlas_adjusted/images/) · [Labels](../outputs/photo_atlas_adjusted/labels/) · [Gap measurements](../outputs/photo_atlas_adjusted/gap_measurements.json)

The supplied image is copied to `assets/reference/user_digit_strip.png`. The preparation code extracts the visible ink of the ten photographed numerals in order, retains their photographic edge character, and places them in ten equally spaced tiles for the existing cylindrical wheel UV mapping. The photographed gray backgrounds, dividing lines, and outer borders are excluded from the ink mask; the wheel substrate, illumination, geometry and glass remain physically rendered by Blender. This means the atlas uses the supplied numeral shapes but does not reproduce all noise or surface texture in the source photograph. The lower tip of the source 7 meets the border of its tile, so information outside that source crop cannot be recovered.

The worker reads `configs/rolling_numerals_atlas.json` and loads the photo atlas by default. The radius and numeral spacing were adjusted to accommodate the new photographed shapes. An upright, closed 4 comes directly from the supplied strip. In the fixed 4-to-5 view, measured visible-gap / box-height ratios are 0.110 at 25%, 0.114 at 50%, and 0.114 at 75%. Measurements use a dark-pixel crop on the final RGB image and apply only to this particular camera, lighting and digit pair; thresholds, reflections and other glyph shapes may change the values. As before, adjacent-digit slivers are visible at some window edges when stationary.

Five 1200 × 460 3D preview images and five sets of mesh-projected OBBs are included. Atlas extraction tests, source hashes, OBB counts, and image-processing tests passed. Glass refraction is not corrected in the OBB labels. The extracted atlas does not by itself establish real-world photorealism.

To rebuild the atlas from the archived source image, run from the repository root:

```bash
python3 -c "import json; from digitgen.photo_atlas import build_photo_atlas; build_photo_atlas(json.load(open('configs/rolling_numerals_atlas.json')))"
```
