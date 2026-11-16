# Repository-Wide Agent Instructions

## Execution Boundaries — READ FIRST

**These instructions establish coding policies. They do not independently authorize any code modifications or cleanup tasks.**

The following section boundaries are mandatory and must be interpreted literally.

| Sections | Activation | Required behavior |
|---|---|---|
| **0–4** | **ALWAYS ON** | Apply these policies to every task, within the scope of the user's request. |
| **5–7** | **CONDITIONAL ONLY** | Execute these procedures ONLY when the user explicitly requests cleanup, simplification, or behavior-preserving refactoring. |
| **8** | **TASK-DEPENDENT** | Report according to the type of task actually requested. |

### Non-Negotiable Rules

1. **Do not initiate cleanup automatically.** The existence of cleanup instructions in this file is NOT permission to perform cleanup.
2. **Do not interpret "avoid defensive engineering" as "remove existing defensive engineering."** These are separate actions.
3. **Do not execute Sections 5–7 during ordinary development**, including feature implementation, bug fixes, data processing, and routine experimentation, unless cleanup/refactoring is explicitly requested.
4. **Do not expand the current task.** Follow the user's actual request rather than proactively improving unrelated code.
5. **An explicit request for formatting alone does not authorize defensive-code removal.** Apply formatting rules without initiating the cleanup protocol.
6. **Repository-wide cleanup requires an explicit repository-wide cleanup request.** Never infer such authorization from general code-quality instructions.

---

# PART I — ALWAYS-ON POLICIES

**Sections 0–4 apply to every task.**

They define how code should be written, how existing files must be protected, and how experiments should be organized.

**They do not instruct the agent to proactively modify existing code.**

## 0. General Principles and Task Scope

This repository is a research-oriented codebase.

Prioritize:

1. Functional correctness.
2. Human readability.
3. Simplicity.
4. Reproducibility.
5. Minimal unnecessary engineering.

For every task:

- Implement only what the user requested.
- Preserve existing behavior unless a change is requested.
- Avoid unrelated improvements or refactoring.
- Do not add speculative infrastructure.
- Do not proactively clean up legacy code.
- Respect existing research decisions and experimental configurations.

A guideline about code quality applies to code being written or modified as part of the current task. It is not authorization to inspect and rewrite unrelated files.

## 1. Human-Readable Code and Formatting

Write code that a human researcher can easily read, understand, debug, and modify.

### Naming

- Use clear, descriptive variable and function names.
- Prefer meaningful names over unexplained abbreviations.
- Preserve standard mathematical and ML notation where appropriate.
- Maintain consistent naming conventions.
- Avoid unnecessarily verbose names when shorter names are clear.

### Control Flow

- Prefer straightforward and explicit implementations.
- Avoid deeply nested conditionals when simpler alternatives are available.
- Avoid clever one-line expressions that reduce readability.
- Use intermediate variables when they clarify computations.
- Keep logically related operations together.
- Avoid excessively long chains of method calls.
- Avoid unnecessary wrapper functions and classes.

### Functions and Abstractions

- Give functions a clear responsibility.
- Split functions only when doing so improves comprehension or reuse.
- Do not create helper functions for trivial expressions without a clear benefit.
- Avoid speculative abstractions and unnecessary class hierarchies.
- Prefer direct implementations over elaborate engineering patterns.

### Comments and Documentation

- Explain non-obvious logic, mathematical assumptions, and important decisions.
- Keep comments and docstrings concise.
- Do not restate obvious code.
- Preserve meaningful scientific explanations and research notes.
- Do not add documentation merely to make the implementation appear more formal.

### Formatting

For Python:

- Follow established PEP 8 conventions.
- Use consistent four-space indentation.
- Maintain readable whitespace, line breaks, and imports.
- Split long expressions into readable multiline statements.
- Preserve existing conventions where reasonable.

Ruff may be used when available:

    ruff format path/to/file.py

For a non-modifying check:

    ruff format --check path/to/file.py

**Formatting restrictions:**

- Format only files relevant to the current task.
- Do not automatically format the entire repository.
- Do not introduce new mandatory formatting infrastructure.
- Do not perform unrelated code cleanup.
- Preserve program behavior.

## 2. Avoid Introducing Excessive Defensive Engineering

**THIS SECTION IS ALWAYS ON, BUT IT IS PREVENTIVE, NOT A CLEANUP COMMAND.**

Its purpose is to prevent unnecessary complexity in new or currently modified code.

It does NOT authorize removing defensive code from unrelated existing implementations.

Every newly introduced validation should prevent a concrete, realistic failure.

Before adding a check, ask:

- What specific failure does it prevent?
- Is that failure relevant to this operation?
- Has another component already checked the same invariant?
- Is this the appropriate stage for that check?
- Is the complexity justified?

### 2.1 Avoid Redundant Hashing

Do not introduce unnecessary:

- Repeated SHA-256 calculations on unchanged files.
- Multiple checksum comparisons checking the same property.
- Repeated file fingerprint verification.
- Hash manifests created solely for duplicate auditing.
- Hashing outputs just to confirm that they were produced.

Preserve hashing when required for genuine integrity, security, reproducibility, or final artifact delivery.

### 2.2 Avoid Redundant Pixel-Level Verification

Do not introduce unnecessary:

- Pixel-by-pixel comparisons of unchanged images.
- Regeneration of images solely to compare them against existing outputs.
- Reconstruction of completed preprocessing results for redundant verification.
- Repeated decoding of entire datasets purely for auditing.

Preserve pixel comparisons that belong to actual algorithms, scientific evaluation, regression testing, or required transformations.

### 2.3 Avoid Repeated Dataset Validation

Do not introduce unnecessary:

- Repeated recursive dataset scans.
- Duplicate dataset inventory checks.
- Multiple validation layers checking identical invariants.
- Repeated geometry reconstruction solely for auditing.
- Duplicate metadata consistency verification.
- Unused verification reports.

Retain checks directly necessary for correct training, valid annotations, dataset-split integrity, and data safety.

### 2.4 Avoid Excessive Cross-Stage Validation

Each component should perform its own responsibility.

Prefer:

    Input
      -> Essential Input Checks
      -> Core Transformation
      -> Output

Avoid unnecessarily creating:

    Input
      -> Validation
      -> Reconstruction
      -> Repeated Validation
      -> Hash Audit
      -> Additional Verification
      -> Output

Trust established upstream contracts unless a realistic boundary failure requires additional checks.

### 2.5 Avoid Unnecessary Infrastructure

Do not introduce unrequested:

- Approval gates.
- Reviewer tracking.
- Audit frameworks.
- Validation frameworks.
- Complex defensive wrappers.
- Speculative compatibility layers.
- Redundant metadata registries.
- Unnecessary state-management systems.

Do not replace simple implementations with complicated infrastructure without a concrete requirement.

### 2.6 Preserve Necessary Checks

Preserve checks required for:

- Functional correctness.
- Security-sensitive operations.
- Destructive file operations.
- Valid inputs and annotations.
- Genuine data-integrity requirements.
- Dataset-split correctness.
- Correct image-label correspondence.
- Scientific reproducibility when necessary.

**Important: Section 2 governs what the agent should avoid ADDING. Removing existing redundant checks is governed exclusively by Section 5 and requires explicit cleanup authorization.**

## 3. Preserve Repository Organization

**THIS SECTION IS ALWAYS ON.**

Do not:

- Move or rename existing directories without explicit authorization.
- Move or rename source files during unrelated work.
- Restructure existing packages during code cleanup.
- Delete historical experiment folders.
- Delete notebooks or previous research work.
- Modify existing datasets or annotations unless requested.
- Delete checkpoints or experiment results.
- Change existing storage paths without necessity.
- Perform unrelated architectural refactoring.

Additional requirements:

- Modify relevant source code in place.
- Preserve historical experimental artifacts.
- Respect existing uncommitted changes.
- Do not automatically commit, push, or rewrite Git history.
- Repository reorganization requires an explicit user request.

## 4. Experiment Organization

**THIS SECTION IS ALWAYS ON WHEN CREATING, DISPLAYING, OR DOCUMENTING EXPERIMENTS.**

It does NOT instruct the agent to create, rename, or reorganize experiments during unrelated tasks.

### 4.1 Chronological Ordering

- Organize experiment listings chronologically: **oldest first, newest last**.
- Determine order using experiment creation timestamps.
- For new experiments, prefer sortable directory names:

    YYYY-MM-DD_HH-mm-ss_short-description

- Use the `America/Chicago` timezone.
- Ensure new experiment directory names are unique.
- Prefer embedded timestamps or recorded experiment metadata over filesystem modification times.

Example:

    experiments/
    ├── 2026-11-13_09-30-00_baseline/
    ├── 2026-11-14_14-20-10_augmentation/
    └── 2026-11-15_15-51-30_new-experiment/

When presenting experiment listings, sort by timestamp in ascending order. Do not assume every file browser automatically uses this sort order.

### 4.2 Preserve Existing Experiments

- Never overwrite historical experiments.
- Do not rename existing folders solely to enforce timestamp naming.
- Do not reorganize experiment directories to change display order.
- Preserve historical results and configurations.
- Respect existing project-specific naming conventions.

If formal delivery rules require:

    experiment_NNN_short-description

preserve that convention instead of replacing it with timestamp-based naming.

Formal delivery organization takes precedence over the general experiment naming preference.

---

# PART II — CONDITIONAL CLEANUP PROTOCOL

**SECTIONS 5–7 ARE DISABLED BY DEFAULT.**

Execute Sections 5–7 **ONLY WHEN THE USER EXPLICITLY REQUESTS CLEANUP, CODE SIMPLIFICATION, OR BEHAVIOR-PRESERVING REFACTORING.**

Examples that activate this part:

- "Clean up the existing code."
- "Remove excessive defensive engineering."
- "Simplify this worker."
- "Refactor these functions without changing behavior."
- "Perform repository-wide cleanup."

Examples that DO NOT activate this part:

- "Implement this feature."
- "Fix this bug."
- "Run this experiment."
- "Generate this dataset."
- "Explain this function."
- "Add a new worker."
- "Format the indentation in this file."

For ordinary development, follow only the Always-On policies and perform tests appropriate to the requested implementation.

## 5. Conditional Cleanup and Refactoring Procedure

**Activation: EXPLICIT CLEANUP/REFACTORING REQUEST ONLY.**

### 5.1 Identify Scope

Before modifying code:

1. Identify the files, functions, or workers covered by the user's cleanup request.
2. Understand their actual responsibilities.
3. Identify unnecessary defensive mechanisms within that scope.
4. Distinguish core functionality from redundant verification.
5. Avoid expanding the task into unrelated improvements.

For repository-wide cleanup, inspect relevant source code throughout the repository, but do not treat historical datasets, experimental results, checkpoints, or archived artifacts as cleanup targets.

### 5.2 Remove Redundant Defensive Engineering

For explicitly requested defensive-engineering cleanup, remove unnecessary:

- Repeated SHA-256 calculations.
- Duplicate file-integrity verification.
- Redundant pixel-by-pixel image comparisons.
- Repeated full-dataset recursive scans.
- Reconstruction of existing outputs solely for verification.
- Duplicate cross-stage validation.
- Redundant metadata auditing.
- Unnecessary approval and review infrastructure.
- Defensive wrappers that serve no concrete purpose.

Remove obsolete imports, helper functions, and configuration fields that exist only to support the deleted mechanisms.

Do not introduce new validation frameworks, auditing layers, or replacement abstractions.

### 5.3 Preserve Core Functionality

Do not change unless explicitly requested:

- ML algorithms.
- Mathematical computations.
- Model architectures.
- Training behavior.
- Evaluation metrics.
- Data transformations.
- Dataset contents.
- Ground-truth annotations.
- Public interfaces.
- Experiment configurations.
- Relevant random-seed behavior.

Removing a redundant audit may intentionally eliminate that audit's failure condition. This is acceptable only when the audit is genuinely unnecessary and core functionality is preserved.

Do not remove security-critical or correctness-critical checks.

### 5.4 Keep Changes Focused

- Modify only relevant source files.
- Avoid unrelated formatting changes.
- Do not move or reorganize modules.
- Do not introduce new features.
- Do not redesign the architecture.
- Do not perform speculative optimizations.

The purpose is subtractive refactoring, not a general rewrite.

## 6. Mandatory Before-and-After Smoke Testing

**Activation: EXPLICIT CLEANUP/REFACTORING REQUEST ONLY.**

For every cleanup task, verify the affected functionality before and after modification.

### 6.1 Before Editing — Establish Baseline

1. Identify the affected executable workflows.
2. Identify small representative inputs.
3. Run an existing lightweight test or smoke-test path.
4. Record baseline outputs or functional invariants.
5. Preserve the baseline until post-cleanup comparison finishes.

A successful import alone is insufficient when the real processing path can be exercised.

Do not launch expensive GPU training or exhaustive dataset validation.

If no suitable existing test is available, use the smallest temporary test necessary.

Do not create a comprehensive test framework.

### 6.2 Temporary Smoke-Test Storage

Store temporary smoke-test outputs **outside the repository**, using the system temporary directory.

Example:

    <system-temp>/
    └── smoke-test-<unique-id>/
        ├── baseline/
        │   └── output.json
        └── after/
            └── output.json

Requirements:

- Do not create permanent smoke-test output directories in the repository.
- Do not modify real datasets, checkpoints, or historical experiments.
- Keep baseline and post-cleanup outputs until comparison finishes.
- Remove temporary outputs after successful verification.
- If verification fails, preserve only necessary temporary diagnostics and report their location.
- Existing repository tests and fixtures may be reused.

Do not introduce audit manifests or additional test infrastructure merely for cleanup.

### 6.3 After Editing — Verify Behavior

1. Rerun the same smoke tests.
2. Use the same representative inputs.
3. Confirm successful execution.
4. Compare relevant outputs against the baseline.
5. Verify that core behavior remains unchanged.
6. Confirm that no unrelated source files or experimental assets were modified.

For deterministic code, compare representative output values directly.

For nondeterministic ML components, use fixed seeds where supported and compare appropriate functional invariants rather than demanding bit-identical GPU results.

### 6.4 Failure Handling

If a smoke test fails:

1. Identify the responsible change.
2. Correct or revert that change.
3. Rerun the relevant test.
4. Do not continue unrelated cleanup while the regression remains unresolved.

Never modify tests or expected results merely to conceal failures.

If the baseline already fails, distinguish pre-existing failures from new regressions.

If a required test cannot execute, report the affected functionality as `UNVERIFIED`.

Never claim `PASS` without actually executing and passing the relevant smoke tests.

## 7. Strict Cleanup Stopping Rule

**Activation: EXPLICIT CLEANUP/REFACTORING REQUEST ONLY.**

Stop cleanup immediately once all conditions hold:

1. The user-requested cleanup is complete.
2. Relevant smoke tests have passed.
3. Core functionality remains unchanged.
4. Repository organization and historical artifacts are preserved.

**STOP. DO NOT CONTINUE REFACTORING.**

Do not proceed into:

- Unrelated optimization.
- Additional formatting.
- Architecture redesign.
- Directory restructuring.
- New testing frameworks.
- New validation infrastructure.
- Speculative improvements.
- Cleanup outside the requested scope.

If verification fails, fix or revert the responsible changes and retest before declaring completion.

If verification is blocked, report the blocker and unverified status rather than performing unrelated cleanup.

Successful verification is the completion gate, not permission to continue improving unrelated code.

---

# PART III — TASK-DEPENDENT REPORTING

## 8. Completion Report

**THIS SECTION APPLIES TO EVERY TASK, BUT THE REQUIRED REPORT DEPENDS ON TASK TYPE.**

### For Ordinary Development

Report only:

- What was implemented or changed.
- Relevant files.
- Tests actually executed and their results.
- Any blockers or limitations.

Do not generate a cleanup report.

### For Explicit Cleanup/Refactoring

Report:

- Source files modified.
- Redundant defensive mechanisms removed.
- Important checks intentionally retained.
- Smoke-test commands actually executed.
- Baseline versus post-cleanup test results.
- Confirmation that repository organization was preserved.
- Final status: `PASS`, `FAIL`, or `UNVERIFIED`.

Keep the report concise.

Do not generate lengthy auditing documentation unless requested.

Do not automatically commit or push changes.

---

# Final Execution Reminder

**Sections 0–4: ALWAYS ON.**

Follow these policies while completing the user's current task. Never infer permission to proactively clean up existing code.

**Sections 5–7: CONDITIONAL ONLY.**

Execute only after an explicit cleanup, simplification, or behavior-preserving refactoring request. Perform before-and-after smoke tests, then stop when verified.

**Section 8: TASK-DEPENDENT.**

Report what was actually done and tested, according to the requested task.

**The current user request determines the work. This document determines how that work must be performed.**