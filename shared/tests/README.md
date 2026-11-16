<!-- recursive-summary:start -->
## Directory overview

Host-Python unit tests and Blender-only checks for geometry, optics, sampling and mask/prompt integration.

### Files

| File | Role |
|---|---|
| [README.md](README.md) | Directory documentation and this managed overview. |
| [band\_projection\_blender.py](band_projection_blender.py) | No-render integration tests: actual mesh projection under 3D camera/register transforms. |
| [blender\_checks.py](blender_checks.py) | Real-Blender geometry regression checks; no rendering required. |
| [optics\_invariants\_blender.py](optics_invariants_blender.py) | No-render analytic invariants for the axis-aligned protective-cover diagnostic. |
| [rotation\_order\_blender.py](rotation_order_blender.py) | Validate real wheel UV tiles and projected vertical order in Blender. |
| [test\_appearance.py](test_appearance.py) | Tests for appearance. |
| [test\_experiment1\_sampling.py](test_experiment1_sampling.py) | Tests for experiment1 sampling. |
| [test\_final\_refinement.py](test_final_refinement.py) | Tests for final refinement. |
| [test\_geometry.py](test_geometry.py) | Tests for geometry. |
| [test\_prompt\_mask\_integration.py](test_prompt_mask_integration.py) | Check the geometry-to-prompt handoff and independent prompt sampling. |
| [test\_raised\_layout.py](test_raised_layout.py) | Tests for raised layout. |
| [test\_rolling\_atlas.py](test_rolling_atlas.py) | Tests for rolling atlas. |
| [test\_statistical\_geometry\_worker.py](test_statistical_geometry_worker.py) | Tests for statistical geometry worker. |
| [test\_x\_shear.py](test_x_shear.py) | Regression tests for X-only shearing, sampling and projected annotations. |

### Summary

This directory groups the files and subdirectories described above.

<!-- recursive-summary:end -->
