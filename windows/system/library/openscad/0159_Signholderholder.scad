// [FL_INDEX: keywords="openscad, 3d_parametric, Signholderholder, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Signholderholder

// Sign holder base depth.
sign_holder_depth=96;

// Sign holder thickness.
sign_holder_thickness=1.7;

// Bar diameter.
bar_dia=25.4;

// Wall thickness
wall=12;

// Space for hangers
hanger_space=15;

// Wiggle room.
wiggle=0.8;


/* [Hidden] */

inch=25.4;
holder_width = bar_dia+(wiggle+wall)*2;
holder_height = 90 +(wiggle+wall)*2;

module rack_top(w=0.0) {
  rotate([0,90,0])
    cylinder(r=bar_dia/2+w, h=150, center=true, $fn=22);
}
module rack_bottom(w=0.0) {
  translate([0,0,-100]) cylinder(r=bar_dia/2+w, h=100, $fn=22);
}

module rack(w=0.0) {
  rack_top(w);
  rack_bottom(w);
}


module sign(w = 0.0) {
  translate([0,-4.25*inch,0]) cube([3+w, 8.5*inch, 11*inch]);
  translate([-(sign_holder_depth/2)-wiggle,-4.25*inch,0])
   cube([sign_holder_depth+wiggle*2, 8.5*inch, sign_holder_thickness + w]);
}
% rack();
% translate([0,0,bar_dia/2 + wall + wiggle + hanger_space]) sign();

down_offset=20;
out_offset=15;

union() {

  translate([0,0,-50]) {
    translate([holder_width/2-wall/2,holder_width/2-wall/2,0]) 
    # cube([0.4,wall, bar_dia + wall], center=true);
    translate([0,0,-holder_width/2+wall/2]) 
    # cube([bar_dia + wall, holder_width, 0.4], center=true);
  }
  
  difference() {
    union() {
      translate([0,0,bar_dia/2 + wiggle + wall + hanger_space])
	cube([130, holder_width, 25], center=true);
      translate([0,0,bar_dia/2 + wiggle + wall -holder_height/2 + hanger_space])
	cube([holder_width, holder_width, holder_height], center=true);
    }

    translate([0,0,bar_dia/2 + wall + wiggle + hanger_space]) {
      sign(wiggle);
      translate([-38,-4.25*inch,0]) cube([96-20, 8.5*inch, 50]);
    }

    hull() {
      rack_top(wiggle);
      translate([0,-out_offset,-down_offset]) rack_top(wiggle);
    }
    hull() {
      translate([0,-out_offset,-down_offset]) rack_top(wiggle);
      translate([0,-30,-down_offset]) rack_top(wiggle);
    }

    rack(wiggle);

    // for (x=[0 : 10])
    translate([0,0,-49]) rotate([90,0,0]) translate([0,0,50]) rack_bottom();

    translate([0,-holder_width,-49-bar_dia/2-wiggle]) {
      cube([holder_width, holder_width*2, bar_dia+wiggle*3]);
    }
    translate([-bar_dia/2-wiggle/2,-holder_width+bar_dia/2,-bar_dia*2-wiggle]) {
      cube([holder_width, holder_width, bar_dia+wiggle*3]);
    }

    translate([-bar_dia/2+0.05,0,-holder_height+bar_dia]) {
      cube([bar_dia - 0.1, holder_width, holder_width-10]);
    }
  }
}