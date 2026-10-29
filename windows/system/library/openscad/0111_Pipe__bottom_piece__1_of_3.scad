// [FL_INDEX: keywords="openscad, 3d_parametric, Pipe__bottom_piece__1_of_3, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Pipe (bottom piece, 1 of 3)

// ===== file: pipe-maker-bottom.scad =====
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
// Joint Cutout Width
cutOutWidth = 2;

difference(){
union(){
difference(){
	cylinder(r=outerDiameter/2,h=length,$fn=roundness);
	cylinder(r=innerDiameter/2,h=length,$fn=roundness);
}

translate([0,0,length])
	difference(){
		cylinder(
			r=(outerDiameter/2 -((outerDiameter/2-innerDiameter/2)/2) - jointGap/2),
			h=jointLength,
			$fn=roundness
		);
		cylinder(r=innerDiameter/2,h=jointLength,$fn=roundness);
	}
}

translate([-outerDiameter/2,-cutOutWidth/2,length])
	cube(size=[outerDiameter,cutOutWidth,jointLength]);

translate([-cutOutWidth/2,-outerDiameter/2,length])
	cube(size=[cutOutWidth,outerDiameter,jointLength]);
}