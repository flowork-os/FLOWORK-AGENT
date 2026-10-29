// [FL_INDEX: keywords="openscad, 3d_parametric, Heart_Clip, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Heart Clip

// preview[view:south east, tilt:top]

// Thick (2mm) is a bit too stiff for holding multiple sheets of paper.
thickness = 1.0; // [0.5:Really Thin (0.5mm), 1.0:Thin (1mm), 2.0:Thick (2mm), 3.0:Thicker (3mm), 4.0:Really Thick (4mm)]

// Overall length (mm)
length = 64; // [50:100]



use <utils/build_plate.scad>

//for display only, doesn't contribute to final object
build_plate_selector = 2; //[2:Thingomatic, 1: Replicator, 0:Replicator 2, 3:Manual]

//when Build Plate Selector is set to "manual" this controls the build plate x dimension
build_plate_manual_x = 100; //[100:400]

//when Build Plate Selector is set to "manual" this controls the build plate y dimension
build_plate_manual_y = 100; //[100:400]

build_plate(build_plate_selector,build_plate_manual_x,build_plate_manual_y); 



module heart(scale_x = 1) {
	// heart humps
	hump_radius = 10;
	translate([0,-(hump_radius - 0.1),0]) cylinder(thickness,hump_radius,hump_radius);
	translate([0,(hump_radius - 0.1),0]) cylinder(thickness,hump_radius,hump_radius);

	// heart stem
	scale([scale_x,1,1]) {
		difference() {
			hull() {
				translate([1,-17.8,thickness/2]) sphere(thickness/2, $fn = 10);
				translate([1,17.8,thickness/2]) sphere(thickness/2, $fn = 10);
				translate([75,0,thickness/2]) sphere(thickness/2, $fn = 10);
			}
			// remove pointed tip
			translate([56,-10,-4]) cube([30,20,8]);
		}
	}
	// add rounded tip
	translate([(55.4 * scale_x),0,0]) cylinder(thickness,6.6,6.6, $fn = 60);
}

module hole(scale_x = 1) {
	depth = thickness + 4;

	translate([0,0,-2]) {
		// upper eyelet holes
		translate([1,-12,0]) cylinder(depth,5,5, $fn = 60);
		translate([1,12,0]) cylinder(depth,5,5, $fn = 60);

		// long flex slots
		scale([scale_x,1,1]) {
			translate([0,16,0]) rotate([0,0,256.3]) cube([4,56,depth]);
			translate([0,-12,0]) rotate([0,0,-76.3]) cube([4,56,depth]);
		}

		// round hole at the tip
		translate([(55.4 * scale_x),0,0]) cylinder(depth,4,4, $fn = 60);
	}
}

module heart_clip(scale_x = 1) {
	translate([-(54 * scale_x / 2),0,0]) difference() {
		heart(scale_x);
		hole(scale_x);
	}
}

// Scale the clip based on the design length of 64mm.
heart_clip(length / 64);