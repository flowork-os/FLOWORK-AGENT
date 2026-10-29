// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_drink_coaster, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable drink coaster

// Diameter of drink coaster [mm]
outerDiameter=130;

difference() {
	cylinder(h = 8, r=outerDiameter/2, $fn=200);
	translate([0,0,4])
		cylinder(h = 4, r=(outerDiameter/2)-4, $fn=200);
}