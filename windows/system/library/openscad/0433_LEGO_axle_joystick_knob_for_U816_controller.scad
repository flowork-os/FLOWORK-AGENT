// [FL_INDEX: keywords="openscad, 3d_parametric, LEGO_axle_joystick_knob_for_U816_controller, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: LEGO axle joystick knob for U816 controller

include <MCAD/regular_shapes.scad>; 
include <MCAD/lego_compatibility.scad>;

// Minimum of 3.167
knob_height = 9.5;

// Minimum of 6.3
knob_diameter = 6.3;

knob_radius = max(6.3, knob_diameter) / 2;
knob_z = max(3.167, knob_height);

module exterior() {
	union() {
		cylinder(h=3.5, r=2.65, $fs=0.5);
		translate([0, 0, 3.5]) cylinder(h=4.3, r1=2.65, r2=knob_radius, $fs=0.5);
		translate([0, 0, 7.8]) cylinder(h=knob_z, r=knob_radius, $fs=0.5);
	}
}

module interior() {
	union() {
		
		// sleeve for joystick nub, from regular_shapes
		hexagon_prism(height=3.5, radius=2);
		
		// flange for screw
		translate([0, 0, 3.5]) cylinder(h=2.3, r=1.025, $fs=0.5);
		
		// space for screw head (and passage through axle hole)
		translate([0, 0, 5.8]) cylinder(h=2 + knob_z, r=1.8, $fs=0.5);
		
		// LEGO axle socket, from lego_compatibility
		translate([0, 0, 7.8]) axle(knob_z / 9.5); // block_height = 9.5
	}
}

difference() {
	exterior();
	interior();
}