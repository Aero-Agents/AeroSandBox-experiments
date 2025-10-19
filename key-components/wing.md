# Wing Object Documentation

This document explains the `Wing` object and its methods, using the docstrings from the code for clarity.

## Wing Class

The `Wing` class defines a wing, which consists of a collection of cross-sections (`xsecs`). Each cross-section is a 2D slice of the wing and is represented by a `WingXSec` object. Wings are lofted linearly between cross-sections. If the wing is symmetric across the XZ plane, only the right half needs to be defined with `symmetric=True`.

### Constructor
```python
Wing(name=None, xsecs=None, symmetric=False, color=None, analysis_specific_options=None, **kwargs)
```
Defines a new wing object.
- `name`: Optional name for the wing.
- `xsecs`: List of wing cross-sections (`WingXSec` objects).
- `symmetric`: Is the wing symmetric across the XZ plane?
- `color`: Visualization color (Matplotlib formats).
- `analysis_specific_options`: Dictionary of analysis-specific options.

---
## Methods

### `translate(xyz)`
Translates the entire wing by a given vector.
- Returns: New wing object.

### `span(type="yz", include_centerline_distance=False, _sectional=False)`
Computes the span of the wing, with options for different measurement planes and inclusion of centerline distance.
- Returns: Span (float or list).

### `area(type="planform", include_centerline_distance=False, _sectional=False)`
Computes the wing area, with options for planform, wetted, or projected area.
- Returns: Area (float or list).

### `aspect_ratio(type="geometric")`
Computes the aspect ratio of the wing.
- Returns: Aspect ratio (float).

### `is_entirely_symmetric()`
Checks if the wing and all its control surfaces are symmetric.
- Returns: Boolean.

### `mean_geometric_chord()`
Returns the mean geometric chord (S/b).
- Returns: Float.

### `mean_aerodynamic_chord()`
Computes the mean aerodynamic chord length using a generalized methodology.
- Returns: Float.

### `mean_twist_angle()`
Returns the mean twist angle (degrees), weighted by area.
- Returns: Float.

### `mean_sweep_angle(x_nondim=0.25)`
Returns the mean sweep angle (degrees) of the wing, relative to the x-axis.
- Returns: Float.

### `mean_dihedral_angle(x_nondim=0.25)`
Returns the mean dihedral angle (degrees) of the wing, relative to the XY plane.
- Returns: Float.

### `aerodynamic_center(chord_fraction=0.25, _sectional=False)`
Computes the location of the aerodynamic center of the wing.
- Returns: (x, y, z) coordinates (array).

### `taper_ratio()`
Gives the taper ratio of the wing (tip chord/root chord).
- Returns: Float.

### `volume(_sectional=False)`
Computes the volume of the wing.
- Returns: Float or list.

### `get_control_surface_names()`
Gets the names of all control surfaces on the wing.
- Returns: List of strings.

### `set_control_surface_deflections(control_surface_mappings)`
Sets the deflection of all control surfaces based on a mapping.
- Returns: None (in-place).

### `control_surface_area(by_name=None, type="planform")`
Computes the total area of all control surfaces, optionally filtered by name.
- Returns: Float.

### `mesh_body(...)`
Meshes the outer mold line surface of the wing. Returns points and faces arrays for visualization or analysis.
- Returns: Tuple of points and faces arrays.

---
## Notes
- For more details on arguments and options, refer to the docstrings in the code.
- The `Wing` object is designed for flexibility in geometry definition and aerodynamic analysis.
