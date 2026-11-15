# Proposed VLM and obsolete review cleanup

Root: `/Users/ququ/synth_data_digit_box/synthetic-data-for-single-digit-box-OBB`

Awaiting explicit approval. This plan includes VLM visual data and the VLM collage, because VLM was explicitly retired. External Codex deliveries remain outside scope.

Files: 398; size: 96,989,339 bytes.

- `3D_worker/generate_vlm_exp.py`: 1 files, 15,138 bytes
- `3D_worker/exp/VLM_exp`: 306 files, 83,207,560 bytes
- `3D_worker/exp/VLM_blue_blur50_yaw20`: 83 files, 13,704,174 bytes
- `3D_worker/exp/VLM_blue_blur50_yaw20.process.json`: 1 files, 863 bytes
- `3D_worker/__pycache__/generate_vlm_exp.cpython-39.pyc`: 1 files, 12,985 bytes
- `3D_worker/__pycache__/generate_vlm_exp.cpython-313.pyc`: 1 files, 24,407 bytes
- `3D_worker/review_final_stage1.py`: 1 files, 7,976 bytes
- `3D_worker/review_raised_stage1.py`: 1 files, 4,863 bytes
- `3D_worker/review_stage1.py`: 1 files, 4,085 bytes
- `3D_worker/prepare_font_review.py`: 1 files, 2,345 bytes
- `3D_worker/industrial_fonts_review.py`: 1 files, 4,943 bytes

Current scene core and scratch worker live in `3D_worker/scene/` and have been tested independently of VLM. The current photo atlas no longer unconditionally imports font candidates. Retained legacy generation, font and Stage 1 helpers still depend on one another; their future need is unresolved, so they are not deletion candidates. The three Stage 1 review scripts listed only inspect historical stage-specific artifacts. The removed font review scripts only create old optional font comparisons. Other images, annotation data, retained inspection helpers and existing edits are excluded.
