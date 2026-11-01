# Physical rolling direction and digit order

[Direction comparison](../outputs/rotation_order_review/inspection_contact_sheet.png) · [Rendered images](../outputs/rotation_order_review/images/) · [Labels](../outputs/rotation_order_review/labels/) · [Blender mapping test](../outputs/rotation_order_review/rotation_order_test.log)

For downward image motion during an increasing 4-to-5 transition, 5 must enter from the top, while 4 moves down and leaves at the bottom. The reviewed current worker already produces that physical order; reversing the atlas would change the direction or the increment sequence. No atlas reversal was applied.

The comparison shows 3→4, 4→5, and the 9→0 wraparound at 50% transition progress. It uses the current user-supplied photo atlas, physical wheel and camera. The visible tops and bottoms are partial glyphs due to the frame.

A Blender test checks the actual wheel mesh UV tile and the physical positions of the current and following glyph centers at 50% progress for all ten possible transitions. Current glyph centers are below the axle; next glyph centers are above it. The 9→0 transition is explicitly included. A host-side mathematical test also checks all ten transitions. The proofs cover the wheel mapping and physical order; the three images provide visual confirmation for the stated camera.

The digit-band OBBs are in `labels/`. The supplied photo atlas, blur and width settings remain in use; existing images are not changed.
