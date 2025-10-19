# Airplane Object Documentation

This document provides a comprehensive explanation of the `Airplane` object in the codebase, using its docstrings to describe its purpose, attributes, and methods.

## Overview

The `Airplane` class defines an airplane object, which consists mainly of a collection of wings and fuselages. These components are accessible via the `wings` and `fuselages` attributes, which are lists of `Wing` and `Fuselage` objects, respectively.

---

## Class: `Airplane`

### Purpose
Defines a new airplane, including its geometry, reference values, and analysis-specific options.

### Anatomy
- **Wings**: List of `Wing` objects (`Airplane.wings`)
- **Fuselages**: List of `Fuselage` objects (`Airplane.fuselages`)
- **Propulsors**: List of `Propulsor` objects (`Airplane.propulsors`)

### Constructor
```python
Airplane(
    name=None,
    xyz_ref=None,
    wings=None,
    fuselages=None,
    propulsors=None,
    s_ref=None,
    c_ref=None,
    b_ref=None,
    analysis_specific_options=None,
)
```
#### Arguments
- **name**: Optional name for the airplane (useful for debugging).
- **xyz_ref**: Reference point (x, y, z) for moments and stability derivatives (usually center of gravity).
- **wings**: List of `Wing` objects.
- **fuselages**: List of `Fuselage` objects.
- **propulsors**: List of `Propulsor` objects.
- **s_ref**: Reference area (defaults to first wing's area).
- **c_ref**: Reference chord (defaults to first wing's mean aerodynamic chord).
- **b_ref**: Reference span (defaults to first wing's span).
- **analysis_specific_options**: Dictionary of analysis-specific options for modeling assumptions.

---

## Methods

### `mesh_body(method="quad", thin_wings=False, stack_meshes=True)`
Returns a surface mesh of the airplane in (points, faces) format. Can mesh wings as thin surfaces or full 3D bodies. Optionally merges meshes into a single mesh.

#### Args
- **method**: Meshing method.
- **thin_wings**: Mesh wings as thin surfaces if True.
- **stack_meshes**: Merge meshes into a single mesh if True.

### `draw(...)`
Produces an interactive 3D visualization of the airplane using various backends (`matplotlib`, `pyvista`, `plotly`, `trimesh`).

#### Args
- **backend**: Visualization backend.
- **thin_wings**: Use thin-surface representation for wings.
- **show**: Display the object after plotting.
- Other arguments control axis, background, and view settings.

### `draw_wireframe(...)`
Draws a wireframe of the airplane on a Matplotlib 3D axis.

#### Args
- **ax**: Axis to draw on.
- **color**: Wireframe color.
- **thin_linewidth**: Linewidth for thin lines.
- **thick_linewidth**: Linewidth for thick lines.
- **fuselage_longeron_theta**: Angles for fuselage longerons.
- Other arguments control axis, background, and view settings.

### `draw_three_view(axs=None, style="shaded", show=True)`
Draws a standard 4-panel three-view diagram of the airplane using Matplotlib. Returns a 2D array of axes for top, front, side, and isometric views.

#### Args
- **axs**: 2D array of axes (optional).
- **style**: Drawing style (`shaded` or `wireframe`).
- **show**: Show the figure after creating it.

### `is_entirely_symmetric()`
Returns True if the airplane is geometrically symmetric across the XZ-plane.

### `aerodynamic_center(chord_fraction=0.25)`
Computes the approximate location of the aerodynamic center of the wing(s), using a weighted average based on area.

#### Args
- **chord_fraction**: Position along the mean aerodynamic chord (default 0.25).

### `with_control_deflections(control_surface_deflection_mappings)`
Returns a copy of the airplane with specified control surface deflections applied.

#### Args
- **control_surface_deflection_mappings**: Dictionary mapping control surface names to deflections (degrees).

### `generate_cadquery_geometry(minimum_airfoil_TE_thickness=0.001, fuselage_tol=1e-4)`
Uses CADQuery to generate a 3D CAD model of the airplane.

#### Args
- **minimum_airfoil_TE_thickness**: Minimum trailing edge thickness for airfoils.
- **fuselage_tol**: Geometric tolerance for CAD geometry.

---

## Summary
The `Airplane` object provides a flexible and comprehensive way to define, visualize, and analyze airplane geometries, supporting advanced modeling, visualization, and CAD export features. Each method is documented with its purpose and arguments, making it easy to use for aerodynamic and structural analysis workflows.
