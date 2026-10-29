// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_Power_Bus, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable Power Bus

// Number of slots connected together.
slots=10;

// Two buses side by side.
double=1; // [0:no, 1:yes]

// Two buses next to each other.
quad=0; // [0:no, 1:yes]

// The diameter of the threaded rod that connects the bus together.
bus_rod_dia=3.7;

// Maximum cable diameter. Generally doesn't hurt to overestimate a bit.
cable_dia=2;

// Making it look nicer.
invert=0; // [0:normal, 1:show insides, 2:all solid]

/* [Hidden] */
// Number of millimeters per slot.
mm_per_slot=9;

module cyl(d, h, clearance,hole,center=false) {
  n = max(round(2 * d),3);
  if (hole) {
    cylinder(h = h, r = ((d + clearance) / 2) / cos (180 / n), $fn = n, center=center);
  } else {
    cylinder(h=h, r=d/2, $fn=round(5*d), center=center);
  }
}

module cable(hole) {
  color([0.9,0.3,0.3]) {
     cyl(cable_dia+1, 51, 0.5, hole);
  }
  color([0.9,0.9,0.3]) {
    rotate([0,0,45]) cyl(cable_dia, 60, 0.5, hole);
  }
}

module M3(len=10, hole) {
  color([0.3, 0.3, 0.3]) {
    translate([0,0,hole?-33:-3]) {
      cyl(5.5, hole?33:3, 0.5, hole);
    }
    cyl(3, len + (hole?1:0), 0.2, hole);
  }
}

module M3Nut(hole) {
  color([0.8,0.8,0.8]) {
    if (!hole) {
      rotate([0,0,30]) cylinder(h=2.4, r=((5.5)/2) / cos(180/6), $fn=6);
    } else {
      translate([0,0,-0.3]) hull() {
        rotate([0,0,30]) cylinder(h=3, r=((5.9)/2) / cos(180/6), $fn=6);
        translate([0,-20,0]) rotate([0,0,30]) cylinder(h=3, r=((5.9)/2) / cos(180/6), $fn=6);
      }
    }
  }
}

module other_parts(hole) {
  color([0.8,0.8,0.8]) {
    translate([0, -bus_rod_dia/2-cable_dia/2+0.5,0]) {
      rotate([0,90,0]) rotate([0,0,180/8]) {
        cyl(bus_rod_dia, mm_per_slot * (slots + (hole ? 3 : 1)), 0.2, hole, center=true);
      }
    }
  }

  for(i=[0:slots-1]) {
    translate([mm_per_slot*i - mm_per_slot * (slots-1)/2, 0, 0]) {
      translate([0,0,-56.1]) cable(hole);
      rotate([90,0,0]) {
        translate([0,0,-8.5]) M3(10, hole);
        translate([0,0,-5]) M3Nut(hole);
      }
    }
  }
}

module rcube(x, y, z, r) {
  linear_extrude(height=z, convexity=2) {
    hull() {
      if (double) {
        translate([0,0,0]) square([r,r]);
        translate([x-r,0,0]) square([r,r]);
      } else {
        translate([r,r,0]) circle(r=r, $fn=round(r*20));
        translate([x-r,r,0]) circle(r=r, $fn=round(r*20));
      }

      translate([r,y-r,0]) circle(r=r, $fn=round(r*20));
      translate([x-r,y-r,0]) circle(r=r, $fn=round(r*20));
    }
  }
}

module block() {
  block_width=mm_per_slot * (slots+1)+4;
  difference() {
    translate([-block_width/2, -8, -5]) rcube(block_width, 22, 10, 3.5);
    other_parts(true);
  }
}

module block1() {
  if (invert == 1) {
    % block();
    other_parts(false);
  } else if (invert == 2) {
    block();
    other_parts(false);
  } else {
    block();
    % other_parts(false);
  }
}

module block2() {
  translate([0,7,0]) block1();
  if (double) {
    mirror([0,1,0]) translate([0,7,0]) block1();
  }
}

//other_parts(false);
mirror([0,0,1]) translate([0,0,-4.9]) block2();
if (quad) translate([0,0,-4.9]) block2();