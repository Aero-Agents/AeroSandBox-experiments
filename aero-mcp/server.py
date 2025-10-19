import aerosandbox as asb  # AeroSandBox for aerodynamic and structural modeling
import aerosandbox.numpy as np  # AeroSandBox's numpy wrapper for optimization compatibility

from airplane_definition import make_plane

import pickle
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path

mcp = FastMCP("aerosandbox_mcp_server", "0.0.1")


class PlaneDefinition(BaseModel):
    """Schema for defining an airplane with wing geometry parameters."""
    
    span: float = Field(..., description="Total span of the wing [meters]", gt=0)
    
    ys_over_half_span: List[float] = Field(
        ..., 
        description="Array of y-locations of each cross-section, normalized by half-span (0 to 1)",
        min_length=2
    )
    
    chords: List[float] = Field(
        ..., 
        description="Array of chord lengths at each cross-section [meters]",
        min_length=2
    )
    
    twists: List[float] = Field(
        ..., 
        description="Array of twist angles at each cross-section [degrees]",
        min_length=2
    )
    
    offsets: Optional[List[float]] = Field(
        None, 
        description="Array of x-offsets of leading edge at each cross-section [meters]. Defaults to -chords/4"
    )
    
    heave_displacements: Optional[List[float]] = Field(
        None, 
        description="Array of vertical displacements of the shear center at each cross-section [meters]"
    )
    
    twist_displacements: Optional[List[float]] = Field(
        None, 
        description="Array of twist displacements at each cross-section [degrees]"
    )
    
    output_filename: str = Field(
        "airplane.pkl", 
        description="Filename for the saved airplane object (must end in .pkl)"
    )



@mcp.tool()
async def create_airplane(plane_def: PlaneDefinition) -> str:
    """
    Creates an airplane object using AeroSandBox and saves it as a pickle file.
    
    This tool generates a plane with a wing based on the provided geometric parameters
    and saves the resulting airplane object to a .pkl file for later use.

    Args:
        plane_def: PlaneDefinition object containing all wing geometry parameters
        
    Returns:
        A success message confirming the airplane was created and saved
    """
    try:
        # Convert lists to numpy arrays for AeroSandBox compatibility
        ys_over_half_span = np.array(plane_def.ys_over_half_span)
        chords = np.array(plane_def.chords)
        twists = np.array(plane_def.twists)
        
        # Handle optional parameters
        offsets = np.array(plane_def.offsets) if plane_def.offsets is not None else None
        heave_displacements = np.array(plane_def.heave_displacements) if plane_def.heave_displacements is not None else None
        twist_displacements = np.array(plane_def.twist_displacements) if plane_def.twist_displacements is not None else None
        
        # Validate array lengths match
        n_sections = len(ys_over_half_span)
        if len(chords) != n_sections or len(twists) != n_sections:
            return f"Error: ys_over_half_span, chords, and twists must have the same length. Got {n_sections}, {len(chords)}, {len(twists)} respectively."
        
        if offsets is not None and len(offsets) != n_sections:
            return f"Error: offsets must have the same length as ys_over_half_span ({n_sections}). Got {len(offsets)}."
        
        if heave_displacements is not None and len(heave_displacements) != n_sections:
            return f"Error: heave_displacements must have the same length as ys_over_half_span ({n_sections}). Got {len(heave_displacements)}."
        
        if twist_displacements is not None and len(twist_displacements) != n_sections:
            return f"Error: twist_displacements must have the same length as ys_over_half_span ({n_sections}). Got {len(twist_displacements)}."
        
        # Create the airplane using make_plane
        airplane = make_plane(
            span=plane_def.span,
            ys_over_half_span=ys_over_half_span,
            chords=chords,
            twists=twists,
            offsets=offsets,
            heave_displacements=heave_displacements,
            twist_displacements=twist_displacements,
        )
        
        # Ensure filename ends with .pkl
        filename = plane_def.output_filename
        if not filename.endswith('.pkl'):
            filename += '.pkl'
        
        # Save the airplane object as a pickle file
        output_path = Path(filename)
        with open(output_path, 'wb') as f:
            pickle.dump(airplane, f)
        
        # Create success message with airplane details
        success_msg = f"""Airplane successfully created and saved!

Output file: {output_path.absolute()}
Wing span: {plane_def.span} m
Number of cross-sections: {n_sections}
Chord range: {min(chords):.3f} - {max(chords):.3f} m
Twist range: {min(twists):.1f} - {max(twists):.1f} deg"""
        
        if heave_displacements is not None:
            success_msg += f"\nHeave displacement range: {min(heave_displacements):.3f} - {max(heave_displacements):.3f} m"
        
        if twist_displacements is not None:
            success_msg += f"\nTwist displacement range: {min(twist_displacements):.1f} - {max(twist_displacements):.1f} deg"
        
        return success_msg
        
    except Exception as e:
        return f"Error creating airplane: {str(e)}"

if __name__ == "__main__":
    mcp.run()