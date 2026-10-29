// [FL_INDEX: keywords="openscad, 3d_parametric, Parametric__Pyramids__easy_to_print, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: [Parametric] Pyramids (easy to print)

use<utils/build_plate.scad>;
use<solids.scad>;

Pyramid_type = 1; // [1:Isosceles,2:Equilateral]

// In millimiters
Base_side_size = 30; // [10:100]

Pyramid_number = 6; // [1:9]

height = Base_side_size;

dist = height;
num = Pyramid_number;

angle = atan(0.5); // Basic trigonometry

//for display only, doesn't contribute to final object
build_plate(3,200,200);

if(Pyramid_type == 2) translate([0,0,Base_side_size/3]) { // Equilateral

Equilateral_pyramid(height);

if(num > 1)
for(i=[0:num-2])
rotate([0,0,i*90])
  translate([0,dist,0])
    Equilateral_pyramid(height);

if(num > 5)
  for(i=[0:num-6])
    rotate([0,0,45+i*90])
      translate([0,dist*1.5,0])
        Equilateral_pyramid(height);

} else translate([0,0,Base_side_size/2]) { // Isosceles

for(i=[0:num-1])
rotate([0,0,i*90])
  translate([0,dist,0])
    Isosceles_pyramid(height);

if(num > 4)
  for(i=[0:num-5])
    rotate([0,0,45+i*90])
      translate([0,dist*1.5,0])
        Isosceles_pyramid(height);

if(num > 8) // *Yaomingface*
  translate([0,-dist*1.5,0])
     Isosceles_pyramid(height);
}

module Equilateral_pyramid(height) {
    edge = height;
    tinyValue = 0.001;
    rotate([90+45,0,0])
      hull() {
          cube(size=[edge, edge, tinyValue], center=true);
          translate([0, 0, height/2]) cube(size=[tinyValue, tinyValue, tinyValue], center=true);
      }
}

module Isosceles_pyramid(height) {
    edge = height;
    tinyValue = 0.001;
    rotate([+90+angle,0,0])
      hull() {
          cube(size=[edge, edge, tinyValue], center=true);
          translate([0, 0, height]) cube(size=[tinyValue, tinyValue, tinyValue], center=true);
      }
}