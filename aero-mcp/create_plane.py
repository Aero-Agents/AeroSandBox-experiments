import yaml
import aerosandbox.numpy as np

def create_airplane_file():
    """
    Create a plane configuration matching the initial setup from elliptical-wing.py
    This creates a rectangular wing (uniform chord) as the starting point for optimization.
    """

    # ===============================
    # Wing Configuration Parameters
    # ===============================

    # Number of chord sections along the wing span
    # This matches N = 16 from the elliptical-wing.py example
    N = 16

    # The y-locations (span locations) of each section
    # Using sinusoidal spacing for better resolution near the wing tip
    # This matches: section_y = np.sinspace(0, 1, N, reverse_spacing=True)
    section_y = np.sinspace(0, 1, N, reverse_spacing=True)

    # Initial chord distribution: uniform (rectangular wing)
    # This matches: chords = opti.variable(init_guess=np.ones(N))
    chords = np.ones(N)

    # Calculate x-positions to keep the quarter-chord line straight
    # This matches: xyz_le=[−0.25 * chords[i], section_y[i], 0]
    x_le = [float(-0.25 * chord) for chord in chords]

    # All cross-sections at z=0 (planar wing)
    z_le = [0.0] * N

    # No twist (untwisted wing as per elliptical-wing.py assumptions)
    twist = [0.0] * N

    # Using a simple airfoil (the elliptical-wing example doesn't specify airfoils)
    # We'll use NACA 0012 (symmetric airfoil) for all sections
    airfoil = ["naca0012"] * N

    # ===============================
    # Airplane Configuration
    # ===============================

    airplane_config = {
        'name': 'RectangularWing',
        'xyz_ref': [0.0, 0.0, 0.0],  # Reference point at origin
        'wing': {
            'name': 'main_wing',
            'x_le': x_le,
            'y_le': [float(y) for y in section_y],  # Convert to plain Python floats
            'z_le': z_le,
            'chord': [float(c) for c in chords],  # Convert to plain Python floats
            'twist': twist,
            'airfoil': airfoil
        }
    }

    # ===============================
    # Write to YAML File
    # ===============================

    output_path = "./plane-definition/airplane.yaml"

    with open(output_path, 'w') as f:
        # Write header comment
        f.write("# ---------------------------------------------------\n")
        f.write("# AeroSandbox Airplane Definition\n")
        f.write("# Initial rectangular wing (uniform chord distribution)\n")
        f.write("# Matches the setup from elliptical-wing.py example\n")
        f.write("# ---------------------------------------------------\n\n")
        
        # Write airplane name and reference point
        f.write(f"name: {airplane_config['name']}\n")
        f.write(f"xyz_ref: {airplane_config['xyz_ref']}\n\n")
        
        # Write wing configuration with readable formatting
        f.write("wing:\n")
        wing = airplane_config['wing']
        f.write(f"  name: {wing['name']}\n")
        f.write(f"  x_le:    {wing['x_le']}\n")
        f.write(f"  y_le:    {wing['y_le']}\n")
        f.write(f"  z_le:    {wing['z_le']}\n")
        f.write(f"  chord:   {wing['chord']}\n")
        f.write(f"  twist:   {wing['twist']}\n")
        f.write(f"  airfoil: {wing['airfoil']}\n")

    print(f"✓ Created airplane configuration at: {output_path}")
    # print(f"✓ Wing has {N} cross-sections")
    # print(f"✓ Span: {section_y[-1]:.3f} m (half-span, symmetric)")
    # print(f"✓ Uniform chord: {chords[0]:.3f} m")
    # print(f"✓ Wing area (half): {sum(chords[i] * (section_y[min(i+1, N-1)] - section_y[max(i-1, 0)]) / 2 for i in range(N)):.3f} m²")

create_airplane_file()