// [FL_INDEX: keywords="openscad, 3d_parametric, 3d_Cube_Perspective_Illusion, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: 3d Cube Perspective Illusion

cube([2,2,10]);
translate([0,0,10]);
cube([2,12,2]);
translate([0,10,0]) cube([2,2,14]);
translate([0,4,12]) cube([2,8,2]);
translate([0,2,12]) cube([14,2,2]);
translate([14,2,12]) cube([2,14,2]);
translate([4,14,12]) cube([12,2,2]);
translate([4,14,0]) cube([2,2,14]);
translate([4,14,0]) cube([12,2,2]);
translate([16,14,0]) cube([2,2,10]);
translate([16,4,8]) cube([2,12,2]);
translate([16,4,-4]) cube([2,2,12]);
translate([16,4,-4]) cube([2,10,2]);
translate([4,12,-4]) cube([12,2,2]);
translate([2,0,-4]) cube([2,14,2]);
translate([2,0,-4]) cube([12,2,2]);
translate([12,0,-4]) cube([2,2,14]);
translate([0,0,8]) cube([12,2,2]);