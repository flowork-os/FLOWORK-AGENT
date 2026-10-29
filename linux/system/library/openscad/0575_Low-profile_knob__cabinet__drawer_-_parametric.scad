// [FL_INDEX: keywords="openscad, 3d_parametric, Low-profile_knob__cabinet__drawer_-_parametric, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Low-profile knob (cabinet, drawer - parametric)

radius = 18 + 1.5;          // Total radius
height = 8.25 + 1.5 + 0.5;  // Total height

pinch_vofs = 0.5 + 1.5;  // Notch offset from bottom
pinch_hofs = 3.5 + 1.5;  // Notch offset from center
pinch_w = 20 - 2*1.5;    // Notch width
pinch_round = 3.75;      // Notch round corner radius

screw_r = 2.9/2;  // M3 loose tap
screw_d = 7.5;

rounding = 1.5;  // Minkowski sum sphere radius
rounding_bottom_trim = 0.5;

//include <lib/util.scad>
module roundedCube8(dim, r, center=false) {
  width = dim[0];
  height = dim[1];
  depth = dim[2];
  centerx = (center[0] == undef ? center : center[0]);
  centery = (center[1] == undef ? center : center[1]);
  centerz = (center[2] == undef ? center : center[2]);
  translate([r - (centerx ? width/2 : 0), r - (centery ? height/2 : 0), r - (centerz ? depth/2 : 0)]) hull() {
    // Edges (bottom)
    translate([0, 0, 0]) rotate([-90, 0, 0]) cylinder(h = height-2*r,r = r);
    translate([width-2*r, 0, 0]) rotate([-90, 0, 0]) cylinder(h = height-2*r,r = r);
    translate([0, 0, 0]) rotate([0, 90, 0]) cylinder(h = width-2*r, r = r);
    translate([0, height-2*r, 0]) rotate([0, 90, 0]) cylinder(h = width-2*r, r = r);
    // Edges (vertical)
    translate([0, 0, 0]) cylinder(h = depth-2*r, r = r);
    translate([width-2*r, 0, 0]) cylinder(h = depth-3*r, r = r);
    translate([0, height-2*r, 0]) cylinder(h = depth-2*r, r = r);
    translate([width-2*r, height-2*r, 0]) cylinder(h = depth-2*r, r = r);
    // Edges (top): not needed with hull()

    // Corners (bottom)
    translate([0, 0, 0]) sphere(r);
    translate([width-2*r, 0, 0]) sphere(r);
    translate([0, height-2*r, 0]) sphere(r);
    translate([width-2*r, height-2*r, 0]) sphere(r);
    // Corners (top)
    translate([0, 0, depth-2*r]) sphere(r);
    translate([width-2*r, 0, depth-2*r]) sphere(r);
    translate([0, height-2*r, depth-2*r]) sphere(r);
    translate([width-2*r, height-2*r, depth-2*r]) sphere(r);

  }
}

module meniscus(r, h) {
  sphere_r = 0.5*(h+r*r/h);
  //echo(sphere_r);
  difference() {
    translate([0, 0, h-sphere_r]) sphere(r=sphere_r);
    translate([-sphere_r-1, -sphere_r-1, -2*sphere_r-1]) cube([2*sphere_r+2, 2*sphere_r+2, 2*sphere_r+1]);
  }
}

// Adjust notch cutout for Minkowski expansion
notch_w = pinch_w + 2*rounding;
notch_d = 2*radius;
notch_h = height - rounding + rounding/3;
notch_round = pinch_round;

difference() {
  minkowski() {
    difference() {
      // Main shape
      meniscus(radius - rounding, height - rounding - rounding_bottom_trim, $fn=36);
      // Pinch notches
      for (s=[-1,+1]) translate([-notch_w/2, -notch_d/2 + s*(notch_d/2+pinch_hofs-rounding), pinch_vofs - rounding]) roundedCube8([notch_w, notch_d, notch_h], r=notch_round, $fn=12);
      // Screw hole
      //translate([0, 0, -1]) cylinder(r=2.95/2, h=10+1, $fn=18);
    }
    sphere(r=rounding, $fn=9);
  }
  // Screw hole
  translate([0, 0, -rounding-1]) cylinder(r=screw_r, h=screw_d + rounding+1, $fn=18);
  // Bottom adjustment
  translate([-radius-1, -radius-1, -rounding-1-rounding_bottom_trim]) cube([2*radius+2, 2*radius+2, rounding+1]);
}