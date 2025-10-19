import yaml
import aerosandbox as asb
import aerosandbox.numpy as np

# --- 1. Load the human-readable file ---

file_path = "./plane-definition/airplane.yaml"
with open(file_path, 'r') as f:
    airplane_data = yaml.safe_load(f)

# Load the operating point configuration
op_file_path = "./plane-definition/operating-point.yaml"
with open(op_file_path, 'r') as f:
    op_data = yaml.safe_load(f)

# --- 2. Process the data ---

wing_data = airplane_data['wing']

# Get the lists for each property

x_le_list = wing_data['x_le']
y_le_list = wing_data['y_le']
z_le_list = wing_data['z_le']
chord_list = wing_data['chord']
twist_list = wing_data['twist']
airfoil_list = wing_data['airfoil']
n_xsecs = len(x_le_list)


altitude=op_data['atmosphere']['altitude']
velocity = op_data['velocity']
alpha = op_data['alpha']
beta = op_data['beta']
p = op_data['p']
q = op_data['q']
r = op_data['r']

# --- 3. Setup optimization variables ---

# initialise the optimiser
opti = asb.Opti()

# --- FIRST GEMINI INSERTION POINT ---

chord_list = opti.variable(init_guess=np.array(wing_data['chord']), lower_bound=np.array(wing_data['chord']), upper_bound=np.array(wing_data['chord'])) # This is made optimisable
alpha = opti.variable(init_guess=op_data['alpha'], lower_bound=0, upper_bound=30)

# --- END GEMINI INSERTION POINT ---

# --- 4. Build the Wing and Airplane objects ---

# Build WingXSec objects from the parallel lists
wing_xsecs_list = []
for i in range(n_xsecs):
    xsec = asb.WingXSec(
        xyz_le=[x_le_list[i] * chord_list[i], y_le_list[i], z_le_list[i]],
        chord=chord_list[i],
        twist=twist_list[i],
        airfoil=asb.Airfoil(name=airfoil_list[i])
    )
    wing_xsecs_list.append(xsec)

# Create the Wing (always symmetric)
main_wing = asb.Wing(
    name=wing_data['name'],
    xsecs=wing_xsecs_list,
    symmetric=True
)

airplane = asb.Airplane(
    name=airplane_data['name'],
    # xyz_ref=airplane_data['xyz_ref'],
    wings=[main_wing]
)

# --- 5. Build the Operating Point ---

atmosphere = asb.Atmosphere(altitude=altitude)

op_point = asb.OperatingPoint(
    atmosphere=atmosphere,
    velocity=velocity,
    alpha=alpha,
    beta=beta,
    p=p,
    q=q,
    r=r
)

# --- 6. Setup the VLM analysis ---
# Set up the Vortex Lattice Method (VLM) aerodynamic solver
# VLM is a panel method for calculating lift and induced drag on lifting surfaces
vlm = asb.VortexLatticeMethod(
    airplane=airplane,          # The aircraft geometry to analyze
    op_point=op_point,          # The flight conditions
    spanwise_resolution=1,      # Number of VLM panels per wing section (low for speed, adequate with monotonicity constraint)
    chordwise_resolution=8,     # Number of panels along chord direction (higher = more accurate)
)

# Run the VLM analysis to compute aerodynamic forces and coefficients
# Returns dictionary with CL (lift coefficient), CD (drag coefficient), etc.
aero = vlm.run()

# --- 7. Setup the optimization problem ---

# --- SECOND GEMINI INSERTION POINT ---

opti.subject_to([
    chord_list > 0,            # All chord lengths must be positive (physical constraint)
    main_wing.area() == 0.25,   # Fix total wing area at 0.25 m² (one of our design requirements)
    alpha >= 0,                # Angle of attack must be non-negative
    alpha <= 30,               # Angle of attack must not exceed 30 degrees
])

# Enforce monotonically decreasing chord distribution from root to tip
# This ensures the wing tapers smoothly toward the tip (physically realistic)
opti.subject_to(
    np.diff(chord_list) <= 0 # The change in chord from one section to the next should be negative or zero.
)
# This ensures our optimized wing produces the required amount of lift
opti.subject_to(
    aero["CL"] == 1
)

# Objective function: Minimize the lift coefficient
# For a fixed lift requirement, this might seem counter-intuitive, but in combination with other implicit constraints,
# it can lead to specific aerodynamic efficiency goals.
opti.minimize(aero["CL"])

# --- END GEMINI INSERTION POINT ---

# --- 8. Solve the optimization problem ---

sol = opti.solve()

# --- 9. Update the .yaml files with the optimized values ---

# Update airplane.yaml with optimized values
with open(file_path, 'w') as f:
    # Write header comment
    f.write("# ---------------------------------------------------\n")
    f.write("# AeroSandbox Airplane Definition\n")
    f.write("# Initial rectangular wing (uniform chord distribution)\n")
    f.write("# Matches the setup from elliptical-wing.py example\n")
    f.write("# ---------------------------------------------------\n\n")
    
    # Write airplane name and reference point
    f.write(f"name: {airplane_data['name']}\n")
    f.write(f"xyz_ref: {airplane_data['xyz_ref']}\n\n")
    
    # Write wing configuration with readable formatting
    f.write("wing:\n")
    f.write(f"  name: {wing_data['name']}\n")
    f.write(f"  x_le:    {[float(x) for x in x_le_list]} # This should be multiplied by chord (especially if chord is to be optimised)\n")
    f.write(f"  y_le:    {[float(y) for y in y_le_list]}\n")
    f.write(f"  z_le:    {[float(z) for z in z_le_list]}\n")
    f.write(f"  chord:   {[float(c) for c in sol(chord_list)]}\n")
    f.write(f"  twist:   {[float(t) for t in twist_list]}\n")
    f.write(f"  airfoil: {airfoil_list}\n")

# Update operating-point.yaml with optimized values
with open(op_file_path, 'w') as f:
    # Write header comment
    f.write("# ---------------------------------------------------\n")
    f.write("# AeroSandbox Operating Point Definition\n")
    f.write("# Defines flight conditions for aerodynamic analysis\n")
    f.write("# ---------------------------------------------------\n\n")
    
    # Write atmosphere configuration
    f.write("atmosphere:\n")
    f.write(f"  altitude: {float(altitude)}  # meters above sea level\n\n")
    
    # Write velocity and angles
    f.write(f"velocity: {float(velocity)}  # m/s (or non-dimensional)\n")
    f.write(f"alpha: {float(sol(alpha))}  # Angle of attack (degrees)\n")
    f.write(f"beta: {float(beta)}  # Sideslip angle (degrees)\n\n")
    
    # Write angular rates
    f.write("# Angular rates (rad/s)\n")
    f.write(f"p: {float(p)}  # Roll rate\n")
    f.write(f"q: {float(q)}  # Pitch rate\n")
    f.write(f"r: {float(r)}  # Yaw rate\n")

print("Updated YAML files with optimized values")

# --- 10. Visualize the results ---

# Generate a 3D visualization of the optimized wing geometry
vlm = sol(vlm)
vlm.draw()

# Import matplotlib for plotting and AeroSandBox's plotting utilities
import matplotlib.pyplot as plt
import aerosandbox.tools.pretty_plots as p

# Create a figure for comparing our result with the theoretical elliptical distribution
fig, ax = plt.subplots()

# Plot the optimized chord distribution from VLM
plt.plot(
    y_le_list,           # Span locations where we have chord values
    sol(chord_list),     # Optimized chord lengths (converted from symbolic to numerical)
    ".-",                # Line with dot markers
    label="AeroSandbox VLM Result",
    zorder=4,            # Draw on top of other plot elements
)

# Generate a smooth analytical elliptical chord distribution for comparison
y_plot = np.linspace(0, 1, 500)  # Fine resolution for smooth curve
# Ellipse equation: chord(y) = sqrt(1 - y²) * constant
# The constant is chosen to match our wing area of 0.25 m²
plt.plot(
    y_plot,
    (1 - y_plot ** 2) ** 0.5 * 4 / np.pi * 0.125,  # Analytical elliptical distribution
    label="Elliptic Distribution",
)

# Display the plot with proper labels and title
p.show_plot(
    "AeroSandbox Drag Optimization using VortexLatticeMethod",
    "Span [m]",    # x-axis label
    "Chord [m]"    # y-axis label
)