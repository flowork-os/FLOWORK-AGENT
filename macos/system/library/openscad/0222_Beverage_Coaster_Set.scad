// [FL_INDEX: keywords="openscad, 3d_parametric, Beverage_Coaster_Set, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Beverage Coaster Set

rib_height=3;
rib_width=.6;
floor_width=.6;
holder_height=40;

$fa=1;
render() {
coaster();
//two_coasters();
//holder();
//holder_1coaster();
//holder_2coasters();
}

module ribs() {
    difference() { cylinder(h=rib_height, r=41); cylinder(h=3, r=40.4); }
    difference() { cylinder(h=rib_height, r=36); cylinder(h=3, r=35.4); }
    difference() { cylinder(h=rib_height, r=31); cylinder(h=3, r=30.4); }
    difference() { cylinder(h=rib_height, r=26); cylinder(h=3, r=25.4); }
    difference() { cylinder(h=rib_height, r=21); cylinder(h=3, r=20.4); }
    difference() { cylinder(h=rib_height, r=16); cylinder(h=3, r=15.4); }
    difference() { cylinder(h=rib_height, r=11); cylinder(h=3, r=10.4); }
    difference() { cylinder(h=rib_height, r=6);  cylinder(h=3, r=5.4); }
}

module coaster() {
  union() {
    difference() {
      cylinder(h=5, r1=43, r2=49);
      translate([0,0,floor_width]) cylinder(h=5, r1=42, r2=48);
    } 
    ribs();
  }
}

module holder() {
  difference() {
    union() {
      difference() {
        cylinder(h=holder_height, r=50+rib_width);
        translate([0,0,floor_width]) {
          cylinder(h=5, r1=42, r2=48);
          translate([0,0,5]) cylinder(h=holder_height, r=50);
        }
      }
      ribs();
    }
    union() {
      translate([60,0,0]) cylinder(h=holder_height, r=52);
      translate([-60,0,0]) cylinder(h=holder_height, r=52);
    }
  }
}

module two_coasters() {
  translate([-50,0,0]) coaster();
  translate([50,0,0]) coaster();
}

module holder_2coasters() {
  holder();
  translate([-60,0,0]) coaster();
  translate([60,0,0]) coaster();
}

module holder_1coaster() {
  translate([-40,0,0]) {
    holder();
    translate([60,0,0]) coaster();
  }
}