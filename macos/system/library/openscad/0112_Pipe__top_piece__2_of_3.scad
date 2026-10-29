// [FL_INDEX: keywords="openscad, 3d_parametric, Pipe__top_piece__2_of_3, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Pipe (top piece, 2 of 3)

// Outer diameter
outerDiameter = 30;
// Inner diameter
innerDiameter = 25;
// Length
length = 100;
// Roundness resolution
roundness = 250;
// Joint Length
jointLength = 20;
// Gap between joints (Wiggle Room)
jointGap = 0.5;

difference(){
	difference(){
		cylinder(r=outerDiameter/2,h=length,$fn=roundness);
		cylinder(r=innerDiameter/2,h=length,$fn=roundness);
		translate([0,0,length-jointLength])
			cylinder(
				r=(outerDiameter/2 -((outerDiameter/2-innerDiameter/2)/2) + jointGap/2),
				h=jointLength,
				$fn=roundness
			);
	}
}
