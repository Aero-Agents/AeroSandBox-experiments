
# Import AeroSandBox - an optimization framework for aircraft design
import aerosandbox as asb
# Import AeroSandBox's numpy wrapper - compatible with CasADi symbolic math for optimization
import aerosandbox.numpy as np

'''Aerodynamic Shape Optimization
Minimum Induced Drag (Elliptical Wing)
Let's do some aerodynamic shape optimization, using a classic problem:

Find the wing shape that minimizes induced drag, with the following assumptions:

A fixed lift
A fixed wing area
A fixed wing span
An untwisted, uncambered, thin, planar wing
Inviscid, incompressible, irrotational, steady flow
The answer, as any good introductory aerodynamics textbook will teach, is a wing with an elliptical lift distribution. For an untwisted wing (in small angle approximation), this corresponds to an elliptical chord distribution.

Let's pose the problem in AeroSandbox, using the VortexLatticeMethod flow solver.'''


# ===============================
# Optimization Setup & Discretization
# ===============================

# Initialize an optimization environment using CasADi backend
# This creates a symbolic optimization problem that can be solved numerically
opti = asb.Opti()

# Number of chord sections to optimize along the wing span
# More sections = higher fidelity but longer solve time
N = 16

# The y-locations (i.e. span locations) of each section. Note that the span is fixed.
# Using sinspace (sinusoidal spacing) instead of linspace for better resolution near the wing tip
# reverse_spacing=True puts finer resolution at the tip (y=1) where gradients are steeper
section_y = np.sinspace(0, 1, N, reverse_spacing=True)
# Using `sinspace` gives us better resolution near the wing tip.

'''We'll use a simple rectangular wing as our initial guess.'''

# Define chord lengths as optimization variables
# init_guess: Start with uniform chord distribution (rectangular wing)
# The optimizer will adjust these values to minimize induced drag
chords = opti.variable(init_guess=np.ones(N)) # All chords initially guessed as "1".


# ===============================
# Wing Geometry Definition
# ===============================

# Create the wing geometry using AeroSandBox's Wing object
# symmetric=True means the wing is mirrored across the centerline (only need to define one side)
wing = asb.Wing(
    symmetric=True,
    xsecs=[  # List of wing cross-sections (xsecs) at different span locations
        asb.WingXSec(
            xyz_le=[  # Leading edge position [x, y, z] for this cross-section
                -0.25 * chords[i], # x-position: keeps the quarter-chord line straight (common aerodynamic reference)
                section_y[i],      # y-position: our predefined span locations
                0                  # z-position: planar wing (no dihedral/anhedral)
            ],
            chord=chords[i],  # Chord length at this section (optimization variable)
        )
        for i in range(N)  # Create one cross-section for each of our N span locations
    ]
)


# ===============================
# Airplane Object and Constraints
# ===============================

# Create an airplane object containing our wing
# AeroSandBox works with complete airplane definitions (can have multiple wings, fuselage, etc.)
airplane = asb.Airplane(
    wings=[
        wing  # Our optimized wing is the only component
    ]
)

# Add optimization constraints to ensure physically realistic solutions
opti.subject_to([
    chords > 0,            # All chord lengths must be positive (physical constraint)
    wing.area() == 0.25,   # Fix total wing area at 0.25 m² (one of our design requirements)
])


# ===============================
# Monotonicity Constraint (Taper)
# ===============================

'''Next, we'll add a constraint that requires the chord distribution to be monotonically
 decreasing, which is something we know from intuition. We can skip this constraint, but 
 if we do, we need to have more than 1 VLM spanwise section per wing section in order to 
 stabilize the solve (the optimization problem is less-well-posed otherwise, 
 and hence can more easily "fall" into local minima).'''

# Enforce monotonically decreasing chord distribution from root to tip
# np.diff(chords) calculates [chord[1]-chord[0], chord[2]-chord[1], ...]
# This ensures the wing tapers smoothly toward the tip (physically realistic)
opti.subject_to(
    np.diff(chords) <= 0 # The change in chord from one section to the next should be negative or zero.
)


# ===============================
# Operating Point & Aerodynamic Solver
# ===============================

'''We don't know the right angle of attack to get the desired lift coefficient a priori, so we'll make 
that an optimization variable too. Note the easy composability of aerodynamic shape 
optimization and operating point optimization.

Then, we set up and run the VLM solve.'''

# Angle of attack is also an optimization variable
# We need to find the right alpha to achieve our target lift coefficient (CL = 1)
# Bounds: 0-30 degrees is a reasonable range for typical flight conditions
alpha = opti.variable(init_guess=5, lower_bound=0, upper_bound=30)

# Define the flight conditions (operating point) for the aerodynamic analysis
op_point = asb.OperatingPoint(
    velocity=1,  # Arbitrary velocity (problem is non-dimensional, so this doesn't affect results)
    alpha=alpha  # Angle of attack (optimization variable)
)

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


# ===============================
# Objective & Optimization Solve
# ===============================

'''Finally, we add our lift constraint, set the optimization objective to minimize drag, and solve'''

# Constraint: Must generate a lift coefficient of 1.0
# This ensures our optimized wing produces the required amount of lift
opti.subject_to(
    aero["CL"] == 1
)

# Objective function: Minimize the drag coefficient
# For a fixed lift and span, this will find the minimum induced drag configuration
opti.minimize(aero["CD"])

# Solve the optimization problem using IPOPT (Interior Point OPTimizer)
# This finds the chord distribution and angle of attack that minimize drag
sol = opti.solve()


# ===============================
# Visualization of Results
# ===============================

'''Let's visualize our solution.

The following command does an in-place substitution of our VLM object, recursively evaluating all
 its fields from abstract values to concrete ones (i.e., NumPy arrays) at our solution, using our 
 sol object.'''

# Substitute the optimized solution values into the VLM object
# This converts symbolic optimization variables to their solved numerical values
vlm = sol(vlm)

# Generate a 3D visualization of the optimized wing geometry
vlm.draw()


# ===============================
# Comparison to Analytic Solution
# ===============================

'''Looking at our optimized solution, we can compare it to our known analytic solution 
(an elliptical lift distribution).'''

# Import matplotlib for plotting and AeroSandBox's plotting utilities
import matplotlib.pyplot as plt
import aerosandbox.tools.pretty_plots as p

# Create a figure for comparing our result with the theoretical elliptical distribution
fig, ax = plt.subplots()

# Plot the optimized chord distribution from VLM
plt.plot(
    section_y,           # Span locations where we have chord values
    sol(chords),         # Optimized chord lengths (converted from symbolic to numerical)
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


# ===============================
# Induced Drag Comparison (Theory vs Computation)
# ===============================

'''Slight differences arise due to numerical discretization, but it's convergent to the 
right answer. We can also check the objective function (the induced drag at the minimum):'''

# Calculate the theoretical minimum induced drag coefficient using classical formula
# For an elliptical lift distribution: CDi = CL² / (π * AR)
# where AR (aspect ratio) = span² / area
AR = 2 ** 2 / 0.25     # Aspect ratio: span = 2m (symmetric, so total = 2*1), area = 0.25 m²
CL = 1                  # Our target lift coefficient

CDi_theory = CL ** 2 / (np.pi * AR)      # Theoretical minimum induced drag (Prandtl's result)
CDi_computed = sol(aero["CD"])            # Computed drag from our VLM optimization

# Print comparison between theory and computation
print(f"CDi (theory)   : {CDi_theory:.4f}")
print(f"CDi (computed) : {CDi_computed:.4f}")

'''Essentially matching theory. Both theory and computation are expected to have slight errors compared to the exact potential flow solution:

The theory side has small errors due to small-angle approximations and simplification of 3D chordwise effects near the tips
The computational side has small errors due to numerical discretization.
(Both methods neglect thickness effects, too.)'''