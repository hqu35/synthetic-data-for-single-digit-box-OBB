# Completed VLM cleanup

The approved 398 files totaling 96,989,339 bytes were deleted after their hashes, candidate contents, and retained dependencies were rechecked. The deleted paths are listed in `execution.json`. External Codex archives remain untouched.

The scene code and scratch worker were separated into `3D_worker/scene/`. The current photographic atlas does not require an unconditional font-candidate import. The blurry worker and scratch worker each rendered a single test image after deletion, and each produced five OBB labels. Fourteen relevant unit tests passed; retained dependencies and symlinks were checked. The one-image scratch smoke test is not a complete 20-image dataset.

Legacy font and Stage 1 helpers with unresolved dependencies were retained. Existing staged Git state was not modified; deletions are working-tree changes and must be staged explicitly before a future commit if desired.
