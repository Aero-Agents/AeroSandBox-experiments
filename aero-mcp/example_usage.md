# MCP Tool Usage Example

## create_airplane Tool

This MCP server provides a `create_airplane` tool that generates an AeroSandBox airplane object and saves it as a pickle file.

### Tool Parameters

The tool accepts a `PlaneDefinition` object with the following fields:

- **span** (required): Total wing span in meters (must be > 0)
- **ys_over_half_span** (required): List of normalized y-locations (0 to 1) for each cross-section
- **chords** (required): List of chord lengths in meters for each cross-section
- **twists** (required): List of twist angles in degrees for each cross-section
- **offsets** (optional): List of x-offsets of leading edge in meters. Defaults to -chords/4
- **heave_displacements** (optional): List of vertical displacements in meters
- **twist_displacements** (optional): List of twist displacements in degrees
- **output_filename** (optional): Output filename (defaults to "airplane.pkl")

### Example Usage

#### Simple Wing (No Displacements)

```json
{
  "span": 10.0,
  "ys_over_half_span": [0.0, 0.25, 0.5, 0.75, 1.0],
  "chords": [2.0, 1.5, 1.0, 0.5, 0.2],
  "twists": [0.0, 0.0, 0.0, 0.0, 0.0],
  "output_filename": "simple_wing.pkl"
}
```

#### Wing with Aeroelastic Displacements

```json
{
  "span": 10.0,
  "ys_over_half_span": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
  "chords": [2.0, 1.8, 1.5, 1.0, 0.6, 0.2],
  "twists": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
  "heave_displacements": [0.0, 0.24, 0.96, 2.16, 3.84, 6.0],
  "twist_displacements": [0.0, -2.5, -5.0, -7.5, -10.0, -12.5],
  "output_filename": "deformed_wing.pkl"
}
```

### Expected Response

On success, the tool returns a text message like:

```
✅ Airplane successfully created and saved!

Output file: /path/to/airplane.pkl
Wing span: 10.0 m
Number of cross-sections: 5
Chord range: 0.200 - 2.000 m
Twist range: 0.0 - 0.0 deg
Heave displacement range: 0.000 - 6.000 m
Twist displacement range: -12.5 - 0.0 deg
```

### Loading the Saved Airplane

To load and use the saved airplane object in Python:

```python
import pickle

# Load the airplane
with open('airplane.pkl', 'rb') as f:
    airplane = pickle.load(f)

# Use the airplane (e.g., visualize it)
airplane.draw()

# Or run aerodynamic analysis
import aerosandbox as asb
vlm = asb.VortexLatticeMethod(
    airplane=airplane,
    op_point=asb.OperatingPoint(velocity=10, alpha=5)
)
aero = vlm.run()
print(f"CL: {aero['CL']}")
print(f"CD: {aero['CD']}")
```
