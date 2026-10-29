// [FL_INDEX: keywords="openscad, 3d_parametric, Lamp_Shade_Reducer_Ring, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Lamp Shade Reducer Ring

difference() {

union() {

	cylinder(3,29,29);
	cylinder(9,21.7,21.7);

}

	#cylinder(20,15,15);
	translate([0,0,3])
	#cylinder(20,19,19);
}