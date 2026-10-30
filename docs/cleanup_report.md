# Dependency-safe cleanup — completed

The user selected the newest usable version of each worker, then explicitly approved the exact deletion and documentation-link plan in experiment_010. Cleanup is complete.

## Result

- Removed **1,793 files across 25 paths**, totaling **339,555,533 logical bytes (323.83 MiB)**.
- Removed superseded previews, historical workspace result copies, Python caches, Finder metadata and the rejected incomplete 22-image dataset.
- Preserved all active source, configuration, tests, assets, font licenses, user edits and workspace/VCS configuration.
- Preserved the selected register preview (`experiment_009`) and industrial-font candidates (`experiment_006`).
- Preserved `outputs/glass_review`, `outputs/stage1_final_refinement` and `outputs/obb_band_stage1` as required scene/parameter inputs, reproduction references and current annotation-validation evidence.
- Redirected **48 links in four documentation files** to verified existing Codex archive copies. No external experiment archive was deleted or rewritten.
- No candidates changed during the final pre-deletion check; no paths were skipped and no additional paths were deleted.

This is a logical-byte estimate. APFS compression and snapshots can affect actual physical storage reclaimed. No extra backup copies or relocated obsolete trees were created to claim space savings.

## Validation

All **343 retained files** were verified byte-for-byte after deletion and after the test suites, allowing only the approved link changes in four documentation files. The project navigation/status and delivery indexes were then refreshed separately; these administrative edits are recorded in the execution report. No Python source, configuration, image, font, atlas or Blender scene was changed.

- **23 host tests passed.**
- Native Blender band-projection tests passed for independent camera/register poses and joint rigid transforms, without rendering.
- Native glass-optics invariants passed, without rendering.
- All three industrial-font atlas/font checksum pairs verify.
- All 48 replacement archive links resolve.
- Seven retained native Blender scenes were inspected: file textures are packed, there are no linked libraries, and no required external image dependencies are missing.
- The retained source, current assets and direct/transitive dependency paths remain present.

## Evidence

- [Execution result and exact removed paths](../outputs/cleanup_review/execution_report.json)
- [Approved plan snapshot and dependency edges](../outputs/cleanup_review/plan.json)
- [Exact per-file deletion manifest](../outputs/cleanup_review/delete_files.sha256.json)
- [Retained checksum baseline](../outputs/cleanup_review/retained_files.sha256.json)
- [Source dependency graph](../outputs/cleanup_review/source_dependencies.json)
- [Native Blender dependency inspection](../outputs/cleanup_review/native_dependencies.json)
- [Existing archive verification](../outputs/cleanup_review/archive_verification.json)
- [Post-cleanup host tests](../outputs/cleanup_review/post_cleanup_host_tests.log)
- [Post-cleanup band-projection tests](../outputs/cleanup_review/post_cleanup_band_projection.log)
- [Post-cleanup optics tests](../outputs/cleanup_review/post_cleanup_optics.log)

The plan snapshot retains its original planning status as historical approval evidence; `execution_report.json` records the completed execution. Original source/result inventories and hashes are retained for auditability.

## Current state

The register preview still has a 93% projected register footprint and approximately 7% background. The industrial-font comparison and its three candidates remain available. Uncommitted/shared source and all 22 font/atlas/license assets were conservatively kept; no unresolved native dependencies were found.

The 100-image dataset remains paused. Its superseded 22-image partial run was removed with approval, while its generator source and configuration remain. **No render, dataset generation, FLUX/ComfyUI run or training job was started during cleanup.**
