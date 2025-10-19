# VortexLatticeMethod Documentation

This document explains the `VortexLatticeMethod` class and its methods, using the docstrings from the source code.

---

## Class: VortexLatticeMethod

An explicit (linear) vortex-lattice-method aerodynamics analysis.

**Usage Example:**
```python
analysis = asb.VortexLatticeMethod(
    airplane=my_airplane,
    op_point=asb.OperatingPoint(
        velocity=100, # m/s
        alpha=5, # deg
        beta=4, # deg
        p=0.01, # rad/sec
        q=0.02, # rad/sec
        r=0.03, # rad/sec
    )
)
aero_data = analysis.run()
analysis.draw()
```

---

### `__init__`
Initializes the VortexLatticeMethod object with the airplane, operating point, reference point, resolution, and other options.

---

### `run()`
Computes the aerodynamic forces.

**Returns:**
A dictionary with keys:
- 'F_g', 'F_b', 'F_w': Forces in geometry, body, and wind axes [N]
- 'M_g', 'M_b', 'M_w': Moments about geometry, body, and wind axes [Nm]
- 'L', 'Y', 'D': Lift, side force, drag [N] (wind axes)
- 'l_b', 'm_b', 'n_b': Rolling, pitching, yawing moments [Nm] (body axes)
- 'CL', 'CY', 'CD': Lift, sideforce, drag coefficients [-] (wind axes)
- 'Cl', 'Cm', 'Cn': Rolling, pitching, yawing coefficients [-] (body axes)

Nondimensional values are referenced to the airplane's reference values.

---

### `run_with_stability_derivatives(alpha=True, beta=True, p=True, q=True, r=True)`
Computes aerodynamic forces, moments, and stability derivatives.

**Arguments:**
- `alpha`, `beta`, `p`, `q`, `r`: Booleans to select which derivatives to compute.

**Returns:**
A dictionary with the same keys as `run()`, plus stability derivatives (e.g., 'CLa', 'CDa', etc.) and neutral point locations.

---

### `get_induced_velocity_at_points(points)`
Computes the induced velocity at a set of points in the flowfield.

**Args:**
- `points`: Nx3 array of points in geometry axes.

**Returns:**
- Nx3 array of induced velocities at those points (geometry axes).

---

### `get_velocity_at_points(points)`
Computes the total velocity at a set of points in the flowfield.

**Args:**
- `points`: Nx3 array of points in geometry axes.

**Returns:**
- Nx3 array of velocities at those points (geometry axes).

---

### `calculate_streamlines(seed_points=None, n_steps=300, length=None)`
Computes streamlines starting at specific seed points using forward-Euler integration.

**Args:**
- `seed_points`: Nx3 ndarray of starting points (auto-calculated if None)
- `n_steps`: Number of steps to trace (min 2)
- `length`: Approximate total length of streamlines (auto-calculated if None)

**Returns:**
- 3D array: (n_seed_points) x (3) x (n_steps) of streamline data
- Also saved as `VortexLatticeMethod.streamlines`

---

### `draw(...)`
Draws the solution using either Plotly or PyVista backends. Must be called on a solved object.

**Args:**
- Various options for coloring, streamlines, backend, etc.

---

## Summary

The `VortexLatticeMethod` class provides a comprehensive interface for vortex-lattice-method aerodynamic analysis, including force/moment computation, stability derivatives, flow visualization, and more. Each method is documented above using its own docstring.
