# Dependency-safe cleanup plan

Status: **awaiting deletion approval. No files have been deleted.**

Root: `/Users/ququ/synth_data_digit_box/synthetic-data-for-single-digit-box-OBB`

## Selected versions

- Register: `outputs/tight_framing_preview` — experiment_009.
- Industrial fonts: `outputs/industrial_fonts_review` — experiment_006.

## What stays

All active source, configuration, assets, licenses, tests, uncommitted work and workspace/VCS configuration remain. The five output folders listed below remain intact because they are selected results or current runtime/reproduction/validation dependencies:

- `outputs/tight_framing_preview` — Selected newest register preview, complete source snapshot and validation.
- `outputs/industrial_fonts_review` — Selected independent font worker result, all three candidate atlases/renders/scenes/licenses.
- `outputs/glass_review` — Live scene and parameter inputs, current optics implementation review and validator inputs.
- `outputs/stage1_final_refinement` — Live font-review source scene and glass-reproduction reference, plus current geometry/ink validation.
- `outputs/obb_band_stage1` — Latest approved band-annotation checkpoint and its validation/approval evidence.

## Exact proposed deletions

Total: **1,793 files, 339,555,533 bytes (323.83 MiB)**. This is a logical byte estimate; filesystem compression and snapshots can affect physical space reclaimed.

| Root-relative path | Files | MiB | Reason |
|---|---:|---:|---|
| `__pycache__` | 21 | 0.18 | Regenerable Python bytecode cache; no source or source-of-record data. |
| `diffusion_model_dataset/exp1` | 74 | 17.00 | Rejected environmental framing; incomplete 22-pair run explicitly superseded by the tight framing preview. Generator/configuration source remains preserved; batch stays paused. |
| `digitgen/__pycache__` | 34 | 0.23 | Regenerable Python bytecode cache; no source or source-of-record data. |
| `outputs/.DS_Store` | 1 | 0.01 | Finder metadata or superseded automatic Blender save backup; no retained live dependency. |
| `outputs/development` | 771 | 125.78 | Historical smoke, lighting, rolling and initial-result iterations superseded by the retained final worker results; no retained entrypoint reads these outputs. |
| `outputs/glass_preview` | 18 | 8.02 | Intermediate preview superseded by the retained final review. |
| `outputs/glass_preview2` | 18 | 7.96 | Intermediate preview superseded by the retained final review. |
| `outputs/quality_preview` | 11 | 1.61 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `outputs/replay10` | 11 | 0.73 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `outputs/rolling` | 38 | 4.30 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `outputs/stage1_final_preview` | 3 | 2.33 | Intermediate preview superseded by the retained final review. |
| `outputs/stage1_final_preview2` | 7 | 3.82 | Intermediate preview superseded by the retained final review. |
| `outputs/stage1_geometry` | 15 | 10.21 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `outputs/stage1_geometry_first` | 11 | 7.22 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `outputs/stage1_raised_band` | 16 | 10.64 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `outputs/stage1_raised_band_first` | 9 | 7.06 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `outputs/upgrade50` | 309 | 53.35 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `outputs/upgrade_diagnostics` | 75 | 17.76 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `outputs/upgrade_quality` | 12 | 2.08 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `outputs/upgrade_replay24` | 13 | 1.03 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `outputs/upgrade_rolling` | 43 | 5.38 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `outputs/upgrade_smoke` | 18 | 1.98 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `outputs/validation50` | 258 | 35.09 | Superseded baseline/mechanical result; newer approved geometry, glass, band OBBs and framing are retained. |
| `tests/__pycache__` | 6 | 0.02 | Regenerable Python bytecode cache; no source or source-of-record data. |
| `tools/__pycache__` | 1 | 0.01 | Regenerable Python bytecode cache; no source or source-of-record data. |

## Dependencies and validation

The preview reads the glass scene and neutral parameters under `outputs/glass_review`. The font worker reads `outputs/stage1_final_refinement/final_stage1_review.blend`. The glass rebuild also reads its corresponding inspection report. Config inheritance, atlas/font hashes, shared imports and current regression fixtures were inspected. These required older folders are not deletion candidates.

The local source graph contains 51 modules; the selected runtime/review entrypoints have a 30-module transitive import closure. All additional active/uncommitted source remains conservatively retained. Seven retained native Blender scenes were opened read-only with automatic scripts disabled: all file textures are packed, no linked libraries are present, and no required external images are missing. All 23 host tests pass. No images were rendered.

Each deletion file and retained file has a SHA-256 snapshot. Before executing, candidate contents must still match the exact plan; retained files must still match afterward. No root-wide wildcard, Git reset or blanket Git clean is proposed.

## Archived results and documentation links

The old published Codex experiments remain outside the cleanup scope. All 258 files from workspace `validation50`, all 309 from `upgrade50`, all 15 from `stage1_geometry` and all 16 from `stage1_raised_band` match their existing archived copies exactly. Other published supplements are retained in the same external archives.

4 current navigation documents need 48 artifact-link changes to their verified archived counterparts. The exact replacements are in `plan.json`; immutable external history is not edited. Existing broken historical links, if any, are identified separately rather than invented or silently repaired.

## Paused dataset

The 22-pair environmental-framing batch is incomplete and rejected. Its status and completion count are recorded in the plan as version-identification evidence. Its generated images/labels/metadata are proposed for deletion; generator source and configuration remain. The batch will not be resumed.

## Review files

- [Exact machine-readable plan and dependency edges](../outputs/cleanup_review/plan.json)
- [Per-file deletion manifest](../outputs/cleanup_review/delete_files.sha256.json)
- [Retained-file checksum baseline](../outputs/cleanup_review/retained_files.sha256.json)
- [Full recursive file inventory](../outputs/cleanup_review/inventory.json)
- [Local import graph](../outputs/cleanup_review/source_dependencies.json)
- [Native project dependency inspection](../outputs/cleanup_review/native_dependencies.json)
- [Archived-copy verification](../outputs/cleanup_review/archive_verification.json)
- [23-test preflight log](../outputs/cleanup_review/preflight_tests.log)

Approval authorizes only the listed deletions and the listed current documentation link updates. No cleanup has been executed.
