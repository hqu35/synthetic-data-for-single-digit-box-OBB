# Delivery organization

The user requires final deliverables outside this source workspace, organized as:

`/Users/ququ/Documents/Codex/YYYY-MM-DD/synthetic-data-for-single-digit-box-OBB/experiment_NNN_short-description/`

- Use the delivery date in America/Chicago, unless the user specifies otherwise.
- Create a NEW experiment directory for every delivered batch or revision, including
  repeated work in this same workspace. Never overwrite or merge with an earlier delivery.
- Increment the experiment number across this project's dated Codex directories.
- Keep source code, assets and temporary/debug outputs in this repository. Publish a
  verified copy of final artifacts to the experiment folder; preserve originals and
  earlier links unless the user explicitly asks for deletion or relocation.
- Use `tools/deliver_results.py` to create an indexed, checksum-verified delivery.
  Pass its `--report` and optional `--extra NAME=SOURCE` arguments as appropriate.
- Each delivery needs a README entry point, results, relevant report, provenance and
  SHA-256 manifest. Adjust copied report links so they open the copied artifacts.
- In the final response, explicitly state and link the absolute experiment path.
- Writing to the external Codex directory may require sandbox escalation. The user
  has authorized this destination; do not ask them to repeat that preference.

## Current scope gate

The user approved Stage II after reviewing the corrected numeral-band OBBs.
The latest request resumes generation and increases the count to exactly 200
deterministic pairs under `diffusion_model_dataset/exp1`,
with controlled camera, register orientation, lighting and mild appearance
variation. Preserve approved mechanics, font atlas, digit identities, transitions
and native glass. Recompute corrected mesh-derived OBBs after every pose change.
Validate the complete dataset and publish a new independent Codex experiment.
All new deliverables, reports, captions, metadata prose and delivery documents
must be in English. STOP after this dataset; do not run FLUX, ComfyUI, additional
dataset experiments or model training.

## Stage II camera framing clarification

The user stopped the initial Stage II run to clarify framing: use a tight, wide
view of the digit register itself. Approximately 90–95% of the view should show
the register, with only approximately 5–10% background. Do not use a wide
environmental composition. Adjust output aspect ratio, camera fitting and roll
range together as necessary while preserving the complete register and digits.
The first run was stopped after 22 completed pairs. Those superseded generated
artifacts were removed on 2026-10-29 under the explicitly approved cleanup plan;
their identification/completion status is recorded in the cleanup report. Do not
resume that camera configuration or present it as the final Experiment 1 dataset.
The rejected run must not be resumed or used as the new dataset.

The user has now authorized 200 varied camera-angle/lighting images using the
latest tight-framing requirement. Preserve 90–95% projected register coverage
and approximately 5–10% background in every image. Fit each physical camera
and constrain projected in-plane roll as needed; do not revert to environmental
framing. Use `configs/diffusion_exp1_200.json`. Deliver exactly 200 validated
image/label pairs, then stop without FLUX inference or training.

The user found the 200-image batch unsuitable because perspective was not
visibly pronounced. The latest request authorizes modifying the worker and
rendering exactly five moderate, genuinely perspective camera views, each with
digit-band OBB overlays and corresponding labels. Preserve the approved model,
glass, typography and tight register framing as far as geometrically feasible;
record and explain any necessary framing tradeoff. Deliver this review in a
new dated experiment directory and stop. No larger dataset, inference or training
is authorized by this request.
