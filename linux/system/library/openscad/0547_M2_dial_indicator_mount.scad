// [FL_INDEX: keywords="openscad, 3d_parametric, M2_dial_indicator_mount, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: M2 dial indicator mount

/* [General] */
build = "dialmount"; // [dialmount, clamptest]

/* [Clamp] */
// How much extra slop for the clamp. Use the clamptest print to determine the proper value.
clamp_clearance = 0.1;

// How far back you want the clamp to extend. 5mm is about the furthest you can go without hitting the x-axis V rail.
lip_depth = 5;

// How long you want your clamp to be.
clamp_length = 20;

// How thick the clamp walls should be.
wall_thickness = 3;

/* [Indicator] */
// Outer diameter of the indicator dial shaft.
shaft_od = 5;

// How much extra space you need to fit.
shaft_clearance = .2;

// How far off from the gantry face you want the edge of the shaft hole to be offset.
hole_border = 2;



/* [Hidden] */
// Thickness of the gantry along the front.
clamp_gap = 9.65;
hole_radius = shaft_od / 2 + shaft_clearance;
hole_center = hole_border + hole_radius;
slop = 0.1;

module clamp(h, c = clamp_clearance) {
  linear_extrude(height = h)
  difference() {
    translate([-wall_thickness, -wall_thickness])
    square([clamp_gap + c + 2*wall_thickness, lip_depth + wall_thickness]);

    square([clamp_gap + c, lip_depth + slop]);
  }
}

clamp_height = 2*wall_thickness + clamp_gap + clamp_clearance;

module dial_mount() {
  // clamp
  rotate([0, 90, 0])
  translate([wall_thickness, wall_thickness, 0])
  clamp(clamp_length);

  // shelf
  shelf_length = 2 * (hole_border + hole_radius);

  difference() {
    translate([0, -shelf_length, -clamp_height])
    cube([clamp_length, shelf_length, clamp_height]);

    translate([clamp_length / 2, -hole_center, -clamp_height - slop])
    cylinder(h = clamp_height + 2 * slop, r = hole_radius, $fn = 20);
  }
}

module clamp_test() {
  for (i = [0 : 3]) {
    translate([18 * i, 0]) clamp(10, i * .1);
  }
}

if (build == "dialmount") dial_mount();
else clamp_test();