// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_Battery_Tray_with_full_empty_label, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable Battery Tray with full/empty label 

use <write/Write.scad>

// print the tray for empty or full batteries?
_label = "full"; // [empty,full]

// battery diameter (AA-14.5, AAA-10.6 123A-16.8 CR2-15.5)
_diameter = 14.6;

// height of the tray
_height = 15; // [1:80]

// number of battery clusters across
_columns = 3; // [1:12]

// number of battery clusters deep
_rows = 1; // [1:12]

// padding between the clusters of batteries (also affects padding along the edges)
_spacing = 1.2;

// thickness of the base under the batteries
_base = 1;

// radius of corner rounding
_cornerRounding = 4.0;


module batteryQuad(diameter, height) {
	angle = 35;
	r = diameter/2;
	cut = 2*r*sin(angle);
	tan = tan(angle);
	filletCenter = r - r * tan;
	filletCenter2 = r + r * tan;
	filletOffset = r * tan;
	filletRadius = r/cos(angle) - r;

	eps = 0.1;

	difference() {
		union() {
			for (x=[-r,r]) {
				for (y=[-r,r]) {
					translate([x,y,0]) {
						cylinder(r=r, h=height, center=true);
					}
				}
			}
			for (t=[ [ r, 0, 0],
					[-r, 0, 0],
					[ 0, r, 0],
					[ 0,-r, 0] ]) {
				translate(t) {
					cube(size=[cut,cut,height], center=true);
				}
			}
		}
		// round
		for (z=[0:90:270]) {
			rotate([0,0,z]) {
				for(y=[filletOffset, -filletOffset]) {
					translate([0, r+y,0]) {
						cylinder(r=filletRadius, h=height+eps, center=true, $fn=30);
					}
				}	
			}
		}
	}
}

module makeTray(diameter, height, rows, columns, spacing, base, rounding) {
	eps = 0.1;
	rounding = min(rounding, diameter/2 + spacing*2);
	quadSize = 2 * diameter;
	width = (quadSize + spacing) * columns + spacing*2;
	depth = (quadSize + spacing) * rows + spacing*2;
	xstart = -width/2 + spacing*1.5 + quadSize/2;
	ystart = -depth/2 + spacing*1.5 + quadSize/2;

	difference() {
		hull()
		for (x=[-width/2 + rounding, width/2 - rounding])
		for (y=[-depth/2 + rounding, depth/2 - rounding]) {
			translate([x,y])
			cylinder(r=rounding, h=height);
		}
		translate([0,0,height/2 + base]) {
			for (x=[0:1:columns-1])
			for (y=[0:1:rows-1]) {
				translate([xstart + (quadSize + spacing)*x,
							 ystart + (quadSize + spacing)*y,0]) {
					batteryQuad(diameter, height);
				}
			}
		}
	}
}

// a battery icon that is 1 unit in height
module battery_icon(thickness=1, empty=true) {
	width = 19;
	height = 8;
	eps = 0.1;
	scale(1/height) union() {
		// battery corpus
		difference() {
			cube([width, height, thickness], center=true);
			cube([width-2, height-2, thickness+2*eps], center=true);
		}
		// plus terminal
		translate([width/2 + 1/2 - eps, 0, 0])
			cube([1+eps, height/2, thickness], center=true);

		// battery status, represented by progress bar
		if(empty) {
			translate([-7, 0, 0])
				cube([1, height-4, thickness], center=true);
		} else {
			for (i = [-3:4]) {
				translate([2*i-1, 0, 0])
					cube([1, height-4, thickness], center=true);
			}
		}
	}
}

total_depth=((2*_diameter + _spacing) * _rows + _spacing*2);
total_width=((2*_diameter + _spacing) * _columns + _spacing*2);

makeTray(_diameter, _height, _rows, _columns, _spacing, _base, _cornerRounding, $fn=90);
if(_label == "empty") {
	translate([0, -total_depth/2, _height/2])
		rotate([90,0,0])
		write("empty", h=_height/2, t=1.5, center=true, font="write/orbitron.dxf");
	translate([0, total_depth/2, _height/2])
		rotate([90,0,180])
		scale([_height/2, _height/2, _height/2*1.5])
		#battery_icon(empty=true);
} else {
	translate([0, -total_depth/2, _height/2])
		rotate([90,0,0])
		write("full", h=_height/2, t=1.5, center=true, font="write/orbitron.dxf");
	translate([0, total_depth/2, _height/2])
		rotate([90,0,180])
		scale([_height/2, _height/2, _height/2*1.5])
		#battery_icon(empty=false);
}