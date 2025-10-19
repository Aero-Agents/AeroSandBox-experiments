import pickle
import aerosandbox as asb  # AeroSandBox for aerodynamic and structural modeling
import aerosandbox.numpy as np  # AeroSandBox's numpy wrapper for optimization compatibility


# Load the airplane
with open('airplane.pkl', 'rb') as f:
    airplane = pickle.load(f)

# Use the airplane (e.g., visualize it)
# airplane.draw()

# ================================== AERODYNAMIC ANALYSIS ===========================================
# Perform vortex lattice method (VLM) analysis to compute aerodynamic forces
# and moments on the deformed wing geometry

opti = asb.Opti()  # Initialize optimization problem

vlm = asb.VortexLatticeMethod(
    airplane=airplane,
    op_point=asb.OperatingPoint(
        velocity=10,  # Freestream velocity [m/s]
        alpha=5,      # Angle of attack [deg]
    ),
    chordwise_resolution=1,  # Number of chordwise panels per section
    spanwise_resolution=1,   # Number of spanwise panels between stations
)

# Run the aerodynamic analysis
aero = vlm.run()

# reconstruct the chord distribution from the airplane object
wing = airplane.wings[0]
chords = [xsec.chord for xsec in wing.xsecs]
section_y = [xsec.xyz_le[1] for xsec in wing.xsecs]
wing_area = wing.area()
span = wing.span()

def set_chords(new_chords):
    for i in range(len(wing.xsecs)):
        wing.xsecs[i].chord = new_chords[i]

print("Chord distribution (m):", chords)
print("Section y-locations (m):", section_y)
print("Wing area (m^2):", wing_area)
print("Wing span (m):", span)


airplane.draw()
# # set up optimization variables for the chord distribution (this may be where we have an issue)
# chords = opti.variable(init_guess=chords)
# set_chords(chords)

# # Add optimization constraints to ensure physically realistic solutions
# opti.subject_to([
#     chords > 0,            # All chord lengths must be positive (physical constraint)
#     wing.area() == wing_area,   # Fix total wing area at 0.25 m² (one of our design requirements)
# ])




# # ===============================
# # Monotonicity Constraint (Taper)
# # ===============================

# '''Next, we'll add a constraint that requires the chord distribution to be monotonically
#  decreasing, which is something we know from intuition. We can skip this constraint, but 
#  if we do, we need to have more than 1 VLM spanwise section per wing section in order to 
#  stabilize the solve (the optimization problem is less-well-posed otherwise, 
#  and hence can more easily "fall" into local minima).'''

# # Enforce monotonically decreasing chord distribution from root to tip
# # np.diff(chords) calculates [chord[1]-chord[0], chord[2]-chord[1], ...]
# # This ensures the wing tapers smoothly toward the tip (physically realistic)
# opti.subject_to(
#     np.diff(chords) <= 0 # The change in chord from one section to the next should be negative or zero.
# )


# # ===============================
# # Operating Point & Aerodynamic Solver
# # ===============================

# '''We don't know the right angle of attack to get the desired lift coefficient a priori, so we'll make 
# that an optimization variable too. Note the easy composability of aerodynamic shape 
# optimization and operating point optimization.

# Then, we set up and run the VLM solve.'''

# # Angle of attack is also an optimization variable
# # We need to find the right alpha to achieve our target lift coefficient (CL = 1)
# # Bounds: 0-30 degrees is a reasonable range for typical flight conditions
# alpha = opti.variable(init_guess=5, lower_bound=0, upper_bound=30)

# # Define the flight conditions (operating point) for the aerodynamic analysis
# op_point = asb.OperatingPoint(
#     velocity=1,  # Arbitrary velocity (problem is non-dimensional, so this doesn't affect results)
#     alpha=alpha  # Angle of attack (optimization variable)
# )

# # Set up the Vortex Lattice Method (VLM) aerodynamic solver
# # VLM is a panel method for calculating lift and induced drag on lifting surfaces
# vlm = asb.VortexLatticeMethod(
#     airplane=airplane,          # The aircraft geometry to analyze
#     op_point=op_point,          # The flight conditions
#     spanwise_resolution=1,      # Number of VLM panels per wing section (low for speed, adequate with monotonicity constraint)
#     chordwise_resolution=8,     # Number of panels along chord direction (higher = more accurate)
# )

# # Run the VLM analysis to compute aerodynamic forces and coefficients
# # Returns dictionary with CL (lift coefficient), CD (drag coefficient), etc.
# aero = vlm.run()


# # ===============================
# # Objective & Optimization Solve
# # ===============================

# '''Finally, we add our lift constraint, set the optimization objective to minimize drag, and solve'''

# # Constraint: Must generate a lift coefficient of 1.0
# # This ensures our optimized wing produces the required amount of lift
# opti.subject_to(
#     aero["CL"] == 1
# )

# # Objective function: Minimize the drag coefficient
# # For a fixed lift and span, this will find the minimum induced drag configuration
# opti.minimize(aero["CD"])

# # Solve the optimization problem using IPOPT (Interior Point OPTimizer)
# # This finds the chord distribution and angle of attack that minimize drag
# sol = opti.solve()


# # ===============================
# # Visualization of Results
# # ===============================

# '''Let's visualize our solution.

# The following command does an in-place substitution of our VLM object, recursively evaluating all
#  its fields from abstract values to concrete ones (i.e., NumPy arrays) at our solution, using our 
#  sol object.'''

# # Substitute the optimized solution values into the VLM object
# # This converts symbolic optimization variables to their solved numerical values
# vlm = sol(vlm)

# # Generate a 3D visualization of the optimized wing geometry
# vlm.draw()


# # ===============================
# # Comparison to Analytic Solution
# # ===============================

# '''Looking at our optimized solution, we can compare it to our known analytic solution 
# (an elliptical lift distribution).'''

# # Import matplotlib for plotting and AeroSandBox's plotting utilities
# import matplotlib.pyplot as plt
# import aerosandbox.tools.pretty_plots as p

# # Create a figure for comparing our result with the theoretical elliptical distribution
# fig, ax = plt.subplots()

# # Plot the optimized chord distribution from VLM
# plt.plot(
#     section_y,           # Span locations where we have chord values
#     sol(chords),         # Optimized chord lengths (converted from symbolic to numerical)
#     ".-",                # Line with dot markers
#     label="AeroSandbox VLM Result",
#     zorder=4,            # Draw on top of other plot elements
# )

# # Generate a smooth analytical elliptical chord distribution for comparison
# y_plot = np.linspace(0, span/2, 500)  # Centered at y=0 for elliptical distribution
# # Ellipse equation: chord(y) = c_root * sqrt(1 - (2y/span)^2)
# # Find c_root such that total area matches wing_area:
# # Area = integral from -b/2 to b/2 of c_root * sqrt(1 - (2y/b)^2) dy = (pi/4) * c_root * span
# # => c_root = 4 * wing_area / (pi * span)
# c_root = 8 * wing_area / (np.pi * span)
# chord_elliptic = c_root * np.sqrt(1 - (2 * y_plot / span) ** 2)
# plt.plot(
#     y_plot,
#     chord_elliptic,
#     label="Elliptic Distribution",
# )

# # Display the plot with proper labels and title
# p.show_plot(
#     "AeroSandbox Drag Optimization using VortexLatticeMethod",
#     "Span [m]",    # x-axis label
#     "Chord [m]"    # y-axis label
# )


# # ===============================
# # Induced Drag Comparison (Theory vs Computation)
# # ===============================

# '''Slight differences arise due to numerical discretization, but it's convergent to the 
# right answer. We can also check the objective function (the induced drag at the minimum):'''

# # Calculate the theoretical minimum induced drag coefficient using classical formula
# # For an elliptical lift distribution: CDi = CL² / (π * AR)
# # where AR (aspect ratio) = span² / area
# AR = 2 ** 2 / 0.25     # Aspect ratio: span = 2m (symmetric, so total = 2*1), area = 0.25 m²
# CL = 1                  # Our target lift coefficient

# CDi_theory = CL ** 2 / (np.pi * AR)      # Theoretical minimum induced drag (Prandtl's result)
# CDi_computed = sol(aero["CD"])            # Computed drag from our VLM optimization

# # Print comparison between theory and computation
# print(f"CDi (theory)   : {CDi_theory:.4f}")
# print(f"CDi (computed) : {CDi_computed:.4f}")

# '''Essentially matching theory. Both theory and computation are expected to have slight errors compared to the exact potential flow solution:

# The theory side has small errors due to small-angle approximations and simplification of 3D chordwise effects near the tips
# The computational side has small errors due to numerical discretization.
# (Both methods neglect thickness effects, too.)'''