# Import necessary libraries for aerodynamic and structural analysis
import aerosandbox as asb  # AeroSandBox for aerodynamic and structural modeling
import aerosandbox.numpy as np  # AeroSandBox's numpy wrapper for optimization compatibility


def make_wing(
        span: float,
        ys_over_half_span: np.ndarray,
        chords: np.ndarray,
        twists: np.ndarray,
        offsets: np.ndarray = None,
        heave_displacements: np.ndarray = None,
        twist_displacements: np.ndarray = None,
        x_ref_over_chord: float = 0.33,
        airfoil: asb.Airfoil = asb.Airfoil("dae11"),
        color="black",
) -> asb.Wing:
    """
    Generates a wing based on a given set of per-cross-section characteristics.
    
    This function creates a Wing object by defining cross-sections along the span
    with specified geometric and aerodynamic properties. It supports structural
    displacements (heave and twist) for aeroelastic analysis.

    Args:
        span: Span of the wing [meters].

        ys_over_half_span: Array of the y-locations of each cross-section, 
            normalized by half-span. Should be between 0 and 1.

        chords: Array of the chord lengths of each cross-section [meters].

        twists: Array of the twist angles of each cross-section [degrees].

        offsets: Array of the x-offsets of the leading edge of each cross-section [meters]. 
            Defaults to -chords / 4, yielding an unswept quarter-chord.

        heave_displacements: Array of the vertical displacements of the shear center 
            of each cross-section [meters]. Defaults to zero.

        twist_displacements: Array of the twist displacements of each cross-section [degrees], 
            as measured about the shear center. Defaults to zero.

        x_ref_over_chord: The x-location of the shear center (i.e., torsion axis), 
            normalized by the chord. Defaults to 0.33 (approximately at the elastic axis).

        airfoil: The airfoil to use for all cross-sections. Defaults to the DAE11.
        
        color: Color for visualization of the wing. Defaults to "black".

    Returns:
        A Wing object with the specified geometry and displacements.
    """
    # Set default values for optional parameters
    if offsets is None:
        offsets = -chords / 4  # Quarter-chord unswept by default
    if heave_displacements is None:
        heave_displacements = np.zeros_like(ys_over_half_span)
    if twist_displacements is None:
        twist_displacements = np.zeros_like(ys_over_half_span)

    xsecs = []  # Initialize list to store wing cross-sections

    # Create wing cross-sections at each spanwise location
    for i in range(len(ys_over_half_span)):
        # Calculate leading edge position relative to the shear center (reference point)
        xyz_le = np.array([
            -chords[i] * x_ref_over_chord,  # x-position (upstream of shear center)
            ys_over_half_span[i] * (span / 2),  # y-position (spanwise)
            0  # z-position (initially at shear center height)
        ])
        
        # Apply twist rotation about the y-axis (total twist = geometric + displacement)
        xyz_le = np.rotation_matrix_3D(
            angle=np.radians(twists[i] + twist_displacements[i]),
            axis="y"
        ) @ xyz_le
        
        # Translate to final position including offsets and heave displacement
        xyz_le += np.array([
            offsets[i] + chords[i] * x_ref_over_chord,  # Add streamwise offset
            0,  # No additional spanwise offset
            heave_displacements[i]  # Add vertical (heave) displacement
        ])

        # Create wing cross-section with calculated position and properties
        xsecs.append(
            asb.WingXSec(
                xyz_le=xyz_le,  # Leading edge position
                chord=chords[i],  # Chord length
                twist=twists[i] + twist_displacements[i],  # Total twist angle
                airfoil=airfoil,  # Airfoil profile
            )
        )

    # Return complete wing object (symmetric about centerline)
    return asb.Wing(
        symmetric=True,  # Creates mirror image about y=0 plane
        xsecs=xsecs,  # List of wing cross-sections
        color=color,  # Visualization color
    )


# ============================================================================
# EXAMPLE WING GEOMETRY DEFINITION
# ============================================================================
# Define a representative wing with tapered planform for testing

# Wing geometry parameters
span = 10  # Total wing span [m]
ys_over_half_span = np.linspace(0, 1)  # Normalized spanwise stations (root to tip)
chords = np.linspace(2, 0.02) ** 0.5  # Chord distribution (tapered, root to tip) [m]
twists = np.linspace(0, 0)  # Twist distribution [deg] (no geometric twist in this case)
offsets = None  # Use default quarter-chord alignment

# Create the wing in its undeformed (jig) shape
wing = make_wing(
    span=span,
    ys_over_half_span=ys_over_half_span,
    chords=chords,
    twists=twists,
    offsets=offsets,
    color="black",
)


# ============================================================================
# STATIC AEROELASTIC ANALYSIS
# ============================================================================
# Perform a coupled aerodynamic-structural analysis to find the equilibrium
# wing shape under aerodynamic loading

# Gather known structural properties
# Convert normalized spanwise locations to actual distances [m]
ys = ys_over_half_span * (span / 2)

# Define bending stiffness (EI) and torsional stiffness (GJ) distributions
# These are proportional to chord^3, simulating a tube spar with:
# - constant wall thickness
# - constant chord-normalized diameter
EI = chords ** 3 * 20  # Bending stiffness [N⋅m²]
GJ = chords ** 3 * 1   # Torsional stiffness [N⋅m²]

# ============================================================================
# OPTIMIZATION SETUP
# ============================================================================
# Set up optimization problem to find structural displacements that satisfy
# equilibrium between aerodynamic loads and structural response

opti = asb.Opti()  # Initialize optimization problem

# Define heave displacement as an optimization variable
# u represents vertical displacement at each spanwise station [m]
u = opti.variable(
    init_guess=np.linspace(0, 1.5) ** 2,  # Initial guess: parabolic distribution
)

# Define twist displacement as an optimization variable
# theta represents torsional deformation at each spanwise station [deg]
theta = opti.variable(
    init_guess=np.linspace(0, -15),  # Initial guess: linear washout
)

# ============================================================================
# GEOMETRY WITH STRUCTURAL DISPLACEMENTS
# ============================================================================
# Create wing geometry including the structural displacement variables
# This couples the structural model to the aerodynamic model

wing = make_wing(
    span=span,
    ys_over_half_span=ys_over_half_span,
    chords=chords,
    twists=twists,
    offsets=offsets,
    heave_displacements=u,      # Vertical displacement (optimization variable)
    twist_displacements=theta,  # Torsional displacement (optimization variable)
)

# ============================================================================
# AERODYNAMIC ANALYSIS
# ============================================================================
# Perform vortex lattice method (VLM) analysis to compute aerodynamic forces
# and moments on the deformed wing geometry

vlm = asb.VortexLatticeMethod(
    airplane=asb.Airplane(
        name="Aerostructures Test",
        xyz_ref=[0, 0, 0],  # Reference point for moments
        wings=[wing],       # Include the wing with displacement variables
    ),
    op_point=asb.OperatingPoint(
        velocity=10,  # Freestream velocity [m/s]
        alpha=5,      # Angle of attack [deg]
    ),
    chordwise_resolution=1,  # Number of chordwise panels per section
    spanwise_resolution=1,   # Number of spanwise panels between stations
)

# Run the aerodynamic analysis
aero = vlm.run()

# ============================================================================
# HEAVE (BENDING) STRUCTURAL ANALYSIS
# ============================================================================
# Apply Euler-Bernoulli beam theory for bending analysis
# Governing equation: d²(EI⋅d²u/dy²)/dy² = -q(y)
# where q(y) is the distributed vertical load

# Compute first derivative of heave displacement: du/dy (slope)
du = opti.derivative_of(
    variable=u, 
    with_respect_to=ys,
    derivative_init_guess=np.zeros_like(u),
)

# Compute second derivative of heave displacement: d²u/dy² (curvature)
ddu = opti.derivative_of(
    variable=du, 
    with_respect_to=ys,
    derivative_init_guess=np.zeros_like(u),
)
                                                         
# Apply boundary conditions for cantilever beam:
opti.subject_to([
    u[0] == 0,    # No deflection at root (fixed)
    du[0] == 0,   # No slope at root (fixed)
    ddu[-1] == 0, # No moment at tip (free end)
])

# ============================================================================
# COUPLE AERODYNAMIC LOADS TO BENDING STRUCTURE
# ============================================================================
# Enforce equilibrium: the rate of change of shear force equals applied load
# d(EI⋅d²u/dy²)/dy = -V(y), where V is the vertical aerodynamic force

opti.constrain_derivative(
    variable=EI * ddu,  # Bending moment distribution: M = EI⋅d²u/dy²
    with_respect_to=ys,
    derivative=np.concatenate([
        -vlm.forces_geometry[:len(ys) - 1, 2],  # Negative of vertical aerodynamic forces
        0  # Zero force gradient at tip
    ]),
)

# ============================================================================
# TWIST (TORSION) STRUCTURAL ANALYSIS
# ============================================================================
# Apply torsion beam theory
# Governing equation: d(GJ⋅dθ/dy)/dy = -T(y)
# where T(y) is the distributed torque about the elastic axis

# Compute first derivative of twist displacement: dθ/dy (twist rate)
dtheta = opti.derivative_of(
    variable=theta, 
    with_respect_to=ys,
    derivative_init_guess=np.zeros_like(theta),
)

# Apply boundary conditions for cantilever beam:
opti.subject_to([
    theta[0] == 0,    # No twist at root (fixed)
    dtheta[-1] == 0,  # No torque at tip (free end)
])

# ============================================================================
# COUPLE AERODYNAMIC MOMENTS TO TORSION STRUCTURE
# ============================================================================
# Enforce equilibrium: the rate of change of torque equals applied moment
# d(GJ⋅dθ/dy)/dy = -M_y(y), where M_y is the aerodynamic pitching moment

opti.constrain_derivative(
    variable=GJ * dtheta,  # Torque distribution: T = GJ⋅dθ/dy
    with_respect_to=ys,
    derivative=np.concatenate([
        -vlm.moments_geometry[:len(ys) - 1, 1],  # Negative of aerodynamic pitching moments
        0  # Zero moment gradient at tip
    ]),
)

# ============================================================================
# SOLVE THE COUPLED AEROELASTIC SYSTEM
# ============================================================================
# Solve the nonlinear system to find equilibrium displacements where
# structural deformations are consistent with aerodynamic loads

sol = opti.solve()

# ============================================================================
# SOLUTION RESULTS
# ============================================================================
# The solution contains the equilibrium heave (u) and twist (theta) distributions
# that satisfy both structural equilibrium and aerodynamic consistency

print("Static aeroelastic analysis complete!")
print(f"Maximum heave displacement: {np.max(sol(u)):.4f} m")
print(f"Maximum twist displacement: {np.max(np.abs(sol(theta))):.4f} deg")