import aerosandbox as asb  # AeroSandBox for aerodynamic and structural modeling
import aerosandbox.numpy as np  # AeroSandBox's numpy wrapper for optimization compatibility


def make_plane(
        
        span: float,
        ys_over_half_span: np.ndarray,
        chords: np.ndarray,
        twists: np.ndarray,
        offsets: np.ndarray = None,
        heave_displacements: np.ndarray = None,
        twist_displacements: np.ndarray = None,

) -> asb.Airplane:
    """
    Generates a plane with a wing based on a given set of per-cross-section characteristics.
    
    This function creates a Plane object, with a Wing object created by defining cross-sections along the span
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
        A Plane object with a wing with the specified geometry and displacements.
    """
    wing = make_wing(
        span=span,
        ys_over_half_span=ys_over_half_span,
        chords=chords,
        twists=twists,
        offsets=offsets,
        heave_displacements=heave_displacements,      # Vertical displacement (optimization variable)
        twist_displacements=twist_displacements,  # Torsional displacement (optimization variable)
    )

    airplane=asb.Airplane(
            name="Aerostructures Test",
            xyz_ref=[0, 0, 0],  # Reference point for moments
            wings=[wing],       # Include the wing with displacement variables
        )
    return airplane


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