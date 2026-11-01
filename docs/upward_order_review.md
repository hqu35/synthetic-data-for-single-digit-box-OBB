# Corrected upward rolling order

[3→4 sequence and additional examples](../outputs/upward_order_review/inspection_contact_sheet.png) · [4→5 gap checks](../outputs/upward_order_review/gap_contact_sheet.png) · [Images](../outputs/upward_order_review/images/) · [OBB labels](../outputs/upward_order_review/labels/) · [Blender direction test](../outputs/upward_order_review/rotation_order_test.log)

The requested visual order is 3 above 4. An increasing 3→4 transition therefore moves upward: 3 starts centered, rises, and 4 enters from below and reaches the center. The physical atlas tile sequence is reversed around the circumference and the axle rotation sign is reversed together; the visible digits and numeric metadata remain in increasing order. The photographic glyphs are unchanged. The user-selected source, crop settings, atlas order, rotation sign and wheel geometry are captured in `atlas_config.json`.

The five-image sequence sheet shows the beginning, midpoint, and end of 3→4, plus midpoints of 4→5 and 9→0. The 3→4 midpoint visibly places 3 above 4. A Blender test checks actual wheel mesh UV tiles and transformed positions for all ten increments, including 9→0. Seven preview images have mesh-derived band OBB labels. Their apparent edges can still shift slightly through refractive glass.

The earlier 4→5 visible-gap check was repeated after the direction change. For this one camera, pair and lighting, the measured gap / projected box-height ratios at 25%, 50%, and 75% are 0.110, 0.110, and 0.103, respectively. The measurement uses a dark-pixel threshold and fixed crop; other views and glyph pairs can differ. Small fragments of neighboring digits remain visible at some stationary window edges, as in the preceding geometry.

The earlier downward-order review was based on the opposite interpretation and is superseded by this correction. The 3D VLM worker uses the corrected atlas and direction by default. Other generators and their saved outputs are not changed.
