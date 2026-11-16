<!-- recursive-summary:start -->
## Directory overview

Shared geometry, Blender construction, annotation, appearance and sampling modules.

### Files

| File | Role |
|---|---|
| [README.md](README.md) | Directory documentation and this managed overview. |
| [\_\_init\_\_.py](__init__.py) | Geometry-derived training data for mechanical digit-slot localization. |
| [assets.py](assets.py) | Implementation module; see its functions and callers for details. |
| [band\_annotations.py](band_annotations.py) | Mesh-derived visible numeral-band annotations for the approved raised register. |
| [camera\_appearance.py](camera_appearance.py) | Deterministic camera processing executed inside Blender, using bundled NumPy. |
| [config.py](config.py) | Implementation module; see its functions and callers for details. |
| [experiment1\_sampling.py](experiment1_sampling.py) | Host-testable deterministic parameters for the approved controlled experiment. |
| [experiment1\_scene.py](experiment1_scene.py) | Scene transforms, restrained light variation and rotated-slab diagnostics. |
| [export.py](export.py) | Implementation module; see its functions and callers for details. |
| [geometry.py](geometry.py) | Pure Python image geometry. Pixels use x right, y down; angles clockwise. |
| [glass.py](glass.py) | One closed physical cover, native Cycles dielectric, and optical validation. |
| [materials.py](materials.py) | Video-guide procedural plastic graph, with texture-driven printed ink. |
| [mechanics.py](mechanics.py) | Actual cylindrical UV meshes, beveled rims/pins, and solid apertures. |
| [photo\_atlas.py](photo_atlas.py) | Extract the user's photographed numerals into the wheel's repeating ink atlas. |
| [pin\_calibration.py](pin_calibration.py) | Finite-aperture pin density calibration; no random sampling. |
| [pin\_visibility.py](pin_visibility.py) | Actual Blender pin visibility through a projected solid aperture. |
| [raised\_layout.py](raised_layout.py) | Deterministic dimensions for Stage 1's raised-band mechanical review. |
| [raised\_mechanics.py](raised_mechanics.py) | Two-layer drums: solid recessed base, annular UV band, edge collar and pins. |
| [sampling.py](sampling.py) | Independent reproducible streams for mechanical, material, light and camera groups. |
| [scene.py](scene.py) | Blender-only scene construction and camera projection adapter. |
| [shear.py](shear.py) | Reproducible image-space X shear and geometry-derived OBBs. |

### Summary

This directory groups the files and subdirectories described above.

<!-- recursive-summary:end -->
