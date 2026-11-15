# Shared components

- `assets/`: the current digit atlas and reference image, shared by the Blender workers.
- `configs/`: shared scene, sampling, geometry and atlas configurations.
- `digitgen/`: shared image, geometry, Blender and annotation modules.

Workers read these components directly. Shared documentation, tests, delivery tools, and project requirements are stored here as well. The statistical 2D mask worker is standalone and does not require these components.
