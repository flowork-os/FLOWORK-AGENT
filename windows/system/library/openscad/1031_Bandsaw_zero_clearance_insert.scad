// [FL_INDEX: keywords="openscad, 3d_parametric, Bandsaw_zero_clearance_insert, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Bandsaw zero clearance insert

//------------parameters---------------------------
// diameter of circle
diameter=30;  
// Thickness 
thickness=2;  
// resolution
$fn=90;

//-------------------------------------------------
cylinder (r=diameter/2,h=thickness);