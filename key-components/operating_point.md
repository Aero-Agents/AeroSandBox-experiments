# OperatingPoint

The `OperatingPoint` class represents the instantaneous aerodynamic flight conditions of an aircraft. It encapsulates the state variables and provides methods to compute various aerodynamic properties and perform axis conversions.

## Class Initialization

**`__init__`**

Initializes an `OperatingPoint` instance.

**Arguments:**
- `atmosphere`: The atmosphere object (of type `asb.Atmosphere`). Defaults to sea level conditions.
- `velocity`: The flight velocity, expressed as a true airspeed. [m/s]
- `alpha`: The angle of attack. [degrees]
- `beta`: The sideslip angle. Positive beta implies oncoming air from the pilot's right-hand side. [degrees]
- `p`: The roll rate about the x_b axis. [rad/sec]
- `q`: The pitch rate about the y_b axis. [rad/sec]
- `r`: The yaw rate about the z_b axis. [rad/sec]

---

## Properties and Methods

### `state`
Returns the state variables of this `OperatingPoint` instance as a dictionary. Keys are variable names, values are the variables themselves.

### `get_new_instance_with_state(new_state)`
Creates a new instance of the `OperatingPoint` class from the given state. `new_state` should be a dictionary in the same format as the `state` property.

### `_set_state(new_state)`
Force-overwrites all state variables with a new set (either partial or complete). Intended for private use only.

### `unpack_state(dict_like_state)`
Unpacks a dict-like state into an array-like representation of the state.

### `pack_state(array_like_state)`
Packs an array-like state into a dict representation matching the state variables.

### `__repr__()`
Returns a string representation of the `OperatingPoint` instance, listing all state variables.

### `__getitem__(index)`
Indexes one item from each attribute, returning a new `OperatingPoint` instance with subscripted attributes.

### `__len__()`
Returns the length of vectorized state variables, ensuring consistency.

### `__array__(dtype="O")`
Allows NumPy array creation without infinite recursion in `__len__` and `__getitem__`.

### `dynamic_pressure()`
Returns the dynamic pressure of the working fluid. [Pa]

### `total_pressure()`
Returns the total (stagnation) pressure of the working fluid, accounting for compressibility effects. [Pa]

### `total_temperature()`
Returns the total (stagnation) temperature of the working fluid. [K]

### `reynolds(reference_length)`
Computes the Reynolds number with respect to a given reference length. [unitless]

### `mach()`
Returns the Mach number for the current flight condition.

### `indicated_airspeed()`
Returns the indicated airspeed for the current flight condition, in meters per second.

### `equivalent_airspeed()`
Returns the equivalent airspeed for the current flight condition, in meters per second.

### `energy_altitude()`
Returns the energy altitude for the current flight condition, in meters. This is the altitude at which a stationary aircraft would have the same total energy as the current condition.

### `convert_axes(x_from, y_from, z_from, from_axes, to_axes)`
Converts a vector from one axis frame to another. Supported frames: "geometry", "body", "wind", "stability". Vectorized over both the vector and the `OperatingPoint`.

### `compute_rotation_matrix_wind_to_geometry()`
Computes the 3x3 rotation matrix that transforms from wind axes to geometry axes.

### `compute_freestream_direction_geometry_axes()`
Computes the freestream direction (direction the wind is going to) in the geometry axes.

### `compute_freestream_velocity_geometry_axes()`
Computes the freestream velocity vector in geometry axes.

### `compute_rotation_velocity_geometry_axes(points)`
Computes the effective velocity due to rotation at a set of points. Input: Nx3 array of points. Output: Nx3 array of effective velocities.

---

## Usage Example
```python
op_point = OperatingPoint()
print(op_point)
```

---