import yaml
import aerosandbox as asb

"""
Create an operating point configuration file.
This defines the flight conditions for aerodynamic analysis.
"""

# ===============================
# Operating Point Configuration
# ===============================

# Define the atmosphere at a specific altitude
# Atmosphere properties (pressure, temperature, density) are calculated automatically
altitude = 0  # meters (sea level)

# Flight velocity (m/s)
# For non-dimensional analysis, this can be set to 1
velocity = 1

# Angle of attack (degrees)
# This will be overridden if made an optimization variable
alpha = 5

# Sideslip angle (degrees)
beta = 0

# Angular rates (rad/s)
# p = roll rate, q = pitch rate, r = yaw rate
p = 0
q = 0
r = 0

# ===============================
# Build Configuration Dictionary
# ===============================

op_config = {
    'atmosphere': {
        'altitude': altitude
    },
    'velocity': velocity,
    'alpha': alpha,
    'beta': beta,
    'p': p,
    'q': q,
    'r': r
}

# ===============================
# Write to YAML File
# ===============================

output_path = "./plane-definition/operating-point.yaml"

with open(output_path, 'w') as f:
    # Write header comment
    f.write("# ---------------------------------------------------\n")
    f.write("# AeroSandbox Operating Point Definition\n")
    f.write("# Defines flight conditions for aerodynamic analysis\n")
    f.write("# ---------------------------------------------------\n\n")
    
    # Write atmosphere configuration
    f.write("atmosphere:\n")
    f.write(f"  altitude: {op_config['atmosphere']['altitude']}  # meters above sea level\n\n")
    
    # Write velocity and angles
    f.write(f"velocity: {op_config['velocity']}  # m/s (or non-dimensional)\n")
    f.write(f"alpha: {op_config['alpha']}  # Angle of attack (degrees)\n")
    f.write(f"beta: {op_config['beta']}  # Sideslip angle (degrees)\n\n")
    
    # Write angular rates
    f.write("# Angular rates (rad/s)\n")
    f.write(f"p: {op_config['p']}  # Roll rate\n")
    f.write(f"q: {op_config['q']}  # Pitch rate\n")
    f.write(f"r: {op_config['r']}  # Yaw rate\n")

print(f"✓ Created operating point configuration at: {output_path}")
print(f"✓ Altitude: {altitude} m")
print(f"✓ Velocity: {velocity} m/s")
print(f"✓ Alpha: {alpha}°, Beta: {beta}°")
print(f"✓ Angular rates - p: {p}, q: {q}, r: {r} rad/s")
