// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_solidoodle_alternative_snap_spool_holder, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable solidoodle alternative snap spool holder

part = "lt"; // [rt:Right tower,lt:Left tower,orb:Outer right bracket,olb:Outer left bracket,irb:Inner right bracket,ilb:Inner left bracket,rtb:Right tower with bracket,ltb:Left tower with bracket]

// How you plan to mount the holder
positioning = 1; // [0:Anywhere along top frame,1:Flush against back (notched brackets)]

// Extra length for back lip, when positioning is flush against back
back_lip_extra_length = 2; // [0:5]

// Arm length; pipe distance from top of printer is arm_length*cos(arm_angle) - clip_inner_diameter/2
arm_length = 122;  // [110:180]
// Arm inclination (towards back); default 30
arm_angle = 30; // [5:45]

// Length of base
base_size = 63;  // [63:73]

// Inner diameter of pipe clip
clip_inner_diameter = 26.5; // [26.4:.75in pipe (tight),26.7:.75in pipe (exact),33.2:1in pipe (tight),33.4:1in pipe (exact)]
// Thickness of pipe clip; must be smaller or equal to clip head thickness (keep larger than 4)
clip_thickness = 8.6;
// Diameter of clip end hole
clip_head_inner_diameter = 18; // [0:23]
// Clip end rim size
clip_head_rim_thickness = 0; // [0:10]
// Clip lip thickness
clip_edge_thickness = 1.5;
// Clip rotation; you may want to adjust if you change arm_angle (30-arm_angle will keep gap orientation unchanged)
clip_angle = 0; // [-20:30]
// Clip lip curvature multiplier (1 to 3 recommended; higher is less curved)
clip_lip_curvature = 1.5;
// Arm side buttress base width; may want to adjust if you change arm angle
arm_buttress_width = 10; // [3:15]

/* [Hidden] */

back_pos = (positioning != 0);

// Base parameters
base_d = base_size;
base_h = 10;
base_w = 26.5;
screw_r = 1.25;
screw_dist = 51;

// Arm parameters
arm_len = arm_length;
arm_thk = 4;
arm_w = 15;
arm_rib = 5;
//arm_angle = 30;
arm_butt_w = arm_buttress_width;


// Clip parameters
clip_h = 4;
clip_od = clip_inner_diameter + clip_thickness + clip_head_rim_thickness;
clip_id = clip_head_inner_diameter;
lip_h = 16;  // includes clip_h
lip_od = clip_inner_diameter + clip_thickness;
lip_id = clip_inner_diameter;
lip_edge_thk = clip_edge_thickness;
lip_phi = 120;
lip_dphi = 75 + clip_angle;
lip_gap_phi = 45;
lip_gap_dphi = lip_dphi - lip_gap_phi;
lip_gap_h = 1;
lip_shave_r = lip_od*clip_lip_curvature;

// Solidoodle frame
sd_slack = 0.2;
sd_frame_thk = 1 + sd_slack;   // sheet metal
sd_toph_w = 26 + sd_slack;  // horizontal
sd_backv_w = 45.5 + sd_slack;  // vertical

rivet_r = 6.3/2 + 0.75;
rivet_h = 1 + 0.3;

// Bracket parameters
bracket_len = base_d;
bracket_thk = 2.5;
bracket_screw_r = 1.75;
bracket_screw_head_r = 2.75;
bracket_screw_head_h = 1.25;
bracket_screw_hole_dist = screw_dist;
bracket_screw_hole_ofs = 5;

// Extra
back_lip_len = bracket_thk + sd_frame_thk + back_lip_extra_length;  // same as inner bracket width

// phi <= 180
module cylinder_hollow(h, od, id, phi, d_phi=0) {
  rotate([0,0,d_phi]) difference() {
    cylinder(h, od/2, od/2, $fn=72);
    translate([0,0,-0.1]) cylinder(h+0.2, id/2, id/2, $fn=72);
    if (phi != 0) {
      translate([0,0,-0.1]) linear_extrude(height=h+0.2, twist=0) polygon([[0,0], [od,0], [cos(phi/2)*od, sin(phi/2)*od], [cos(phi)*od, sin(phi)*od]], convexity=2);
    }
  }
}

// phi <= 180
module cylinder_hollow_n(h, od, id, phi, d_phi=0) {
  rotate([0,0,d_phi]) intersection() {
    difference() {
      cylinder(h, od/2, od/2, $fn=72);
      translate([0,0,-0.1]) cylinder(h+0.2, id/2, id/2, $fn=72);
    }
    translate([0,0,-0.1]) linear_extrude(height=h+0.2, twist=0) polygon([[0,0], [od,0], [cos(phi/2)*od, sin(phi/2)*od], [cos(phi)*od, sin(phi)*od]], convexity=2);
  }
}

module buttress_w(thk, w, phi) {
  h = w*tan(phi);
  linear_extrude(height=thk, twist=0) polygon([[0,0],[w,0],[w,h]], convexity=2);
}

module buttress_h(thk, h, phi) {
  w = h/tan(phi);
  linear_extrude(height=thk, twist=0) polygon([[0,0],[w,0],[w,h]], convexity=2);
}




module base(lt_holes=true, rt_holes=true) {
  difference() {
    cube([base_w, base_d, base_h]);
    if (rt_holes) {
      translate([-1, (base_d-screw_dist)/2, base_h/2]) rotate([0,90,0]) cylinder(base_w/2+1+1,screw_r,screw_r, $fn=36);
      translate([-1, (base_d+screw_dist)/2, base_h/2]) rotate([0,90,0]) cylinder(base_w/2+1+1,screw_r,screw_r, $fn=36);
    }
    if (lt_holes) {
      translate([-1+base_w/2, (base_d-screw_dist)/2, base_h/2]) rotate([0,90,0]) cylinder(base_w/2+1+1,screw_r,screw_r, $fn=36);
      translate([-1+base_w/2, (base_d+screw_dist)/2, base_h/2]) rotate([0,90,0]) cylinder(base_w/2+1+1,screw_r,screw_r, $fn=36);
    }
    *union() {  // Test print only 
      translate([-1, -base_d/2-2.5, 0]) cube([base_w, base_d, base_h]);
      translate([-1, base_d/2+2.5, 0]) cube([base_w, base_d, base_h]);
    }
  }
  if (back_pos) {
    translate([0,0,-back_lip_len]) cube([base_w, bracket_thk, back_lip_len+base_h]);
  }
}

module arm(left=0) {
  sb = left;
  ss = 1 - 2*sb;
  l = arm_len - sqrt(clip_od*clip_od - arm_w*arm_w)/2 + 0.2;
  union() {
    // Main
    cube([arm_thk, arm_w, l]);
    // Reinforcement
    translate([-sb*arm_rib + ss*0.05, (arm_w-arm_rib)/2, 0]) cube([arm_thk+arm_rib,arm_rib, l]);
    // Clip buttress
    translate([ss*lip_h + sb*arm_thk, (arm_w+ss*arm_rib)/2, arm_len-lip_od/2+0.2]) rotate([-90,0,(1-sb)*180]) buttress_w(arm_rib,lip_h-arm_rib-arm_thk, 30);
    // Side buttress
    translate([ss*(base_w - 0.1) + sb*arm_thk, (arm_w-ss*arm_rib)/2, base_h/cos(arm_angle)-tan(arm_angle)*(arm_w+arm_rib)/2 - 0.1]) rotate([-90, 180, sb*180]) buttress_w(arm_rib, base_w-arm_rib-arm_thk, 30);
    // Back buttress
    translate([arm_thk,0,base_h/cos(arm_angle)-0.1]) rotate([90,-arm_angle,-90]) linear_extrude(height=arm_thk, twist=0) polygon([[0,0],[arm_butt_w,0],[0.5*arm_butt_w,0.5*arm_butt_w*tan(90-arm_angle)]], convexity=2);
  }
}

module clip(left=0) {
  sb = left;  // 0,1
  ss = 1 - 2*sb;  // 0,1 -> 1,-1
  union() {
    cylinder_hollow(clip_h,clip_od,clip_id,0);
    translate([0,0,-sb*(lip_h-clip_h)]) difference() {
      cylinder_hollow(lip_h, lip_od, lip_id, lip_phi, lip_dphi);
      translate([0,0,sb*(lip_h-clip_h-lip_gap_h)]) cylinder_hollow_n(clip_h+lip_gap_h, lip_od+1, lip_id-1, lip_gap_phi+1, lip_gap_dphi);
      translate([0,0,ss*0.1]) rotate([0,0,lip_dphi-acos((lip_id/2)/(lip_od/2-lip_edge_thk))+0.1]) linear_extrude(height=lip_h+0.2, twist=0) polygon([[0,0], [lip_id/2,0], [lip_id/2, sqrt(pow(lip_od/2-lip_edge_thk,2)-pow(lip_id/2,2))]], convexity=2);
      translate([0,0,ss*0.1]) rotate([0,0,lip_dphi-lip_gap_phi/2]) translate([0.5*lip_od*cos(lip_gap_phi/2)+lip_shave_r*sqrt(1-pow(0.5*sin(lip_gap_phi/2)*lip_od/lip_shave_r,2)), 0, 0]) cylinder(lip_h+0.2, lip_shave_r, lip_shave_r, $fn=144);
    }
    translate([0,0,-sb*(lip_h-clip_h)]) union() {
      rotate([0,0,lip_phi+lip_dphi]) translate([(lip_id+lip_od)/4-0.1,0,0]) cylinder(lip_h, (lip_od-lip_id)/4, (lip_od-lip_id)/4, $fn=32);
      %rotate([0,0, lip_dphi]) translate([(lip_od-lip_edge_thk)/2-0.03, 0, 0]) cylinder(lip_h, lip_edge_thk/2, lip_edge_thk/2, $fn=32);
      // Extra support
      // TODO: radial offset not properly parameterized
      *rotate([0,0, lip_dphi - lip_gap_phi/2]) translate([(lip_od-4*lip_edge_thk)/2, 0, 0]) cylinder(lip_h, lip_edge_thk/2, lip_edge_thk/2, $fn=32);
    }
  }
}

module tower(left=0, lt_holes=true, rt_holes=true) {
  sb = left;  // 0,1
  ss = 1 - 2*sb;  // 0,1 -> 1,-1
  difference() {
    union() {  
      base(lt_holes, rt_holes);
      // Arm and clip assembly
      translate([sb*(base_w-arm_thk), base_d/2, 0]) rotate([arm_angle,0,0]) union() {
        arm(left);
        translate([0, arm_w/2, arm_len]) rotate([0, 90, 0]) clip(left);
      }
    }
    if (back_pos) {
      if (left == 0) {
        translate([0,bracket_thk,-1] + [20,13.5,0]) cylinder(r=rivet_r, h=rivet_h+1);
        translate([0,bracket_thk,-1] + [7,32.5,0]) cylinder(r=rivet_r, h=rivet_h+1);
      } else {
        translate([base_w,bracket_thk,-1]+[-20,13.5,0]) cylinder(r=rivet_r, h=rivet_h+1);
        translate([base_w,bracket_thk,-1]+[-7,32.5,0]) cylinder(r=rivet_r, h=rivet_h+1);
      }
    }
  }
}


module bracket_screw_hole() {
  union() {
    cylinder(bracket_thk+1, bracket_screw_r, bracket_screw_r, $fn=18);
    cylinder(bracket_screw_head_h, bracket_screw_head_r, bracket_screw_r, $fn=18);
    translate([0,0,-1+0.05]) cylinder(1, bracket_screw_head_r, bracket_screw_head_r, $fn=18);
  }
}

module bracket(inner = 0, left=0, holes=true) {
  bb = back_pos ? 1 : 0;
  bracket_w = base_h + bracket_thk + inner*sd_frame_thk + (1-inner)*sd_toph_w;
  difference() {
    union() {
      cube([bracket_w, bracket_thk, bracket_len]);
      translate([bracket_w-bracket_thk,0,bb*(inner*(1-left) + (1-inner)*left)*(sd_backv_w+bracket_thk)]) cube([bracket_thk, 2*bracket_thk, bracket_len-bb*(sd_backv_w+bracket_thk)]);
echo(bracket_len-bb*(sd_backv_w+bracket_thk));
      if (back_pos) {
        if (inner == 0) {
          translate([base_h+back_lip_len,0,(1-left)*(bracket_len-bracket_thk)]) cube([bracket_w-base_h-back_lip_len,bracket_thk+back_lip_len,bracket_thk]);
        } else {
          translate([0,0,left*(bracket_len-bracket_thk)]) cube([base_h+back_lip_len,bracket_thk,bracket_thk]);
        }
      }
    }
    if (holes) {
      translate([bracket_screw_hole_ofs, 0, (bracket_len-bracket_screw_hole_dist)/2]) rotate([-90,0,0]) bracket_screw_hole();
      translate([bracket_screw_hole_ofs, 0, (bracket_len+bracket_screw_hole_dist)/2]) rotate([-90,0,0]) bracket_screw_hole();
    }
    if (back_pos && (inner != 0)) {
      translate([base_h,0,bracket_thk+left*(bracket_len-sd_backv_w-2*bracket_thk)]) cube([bracket_w-base_h, bracket_thk,sd_backv_w]);
    }
    if (back_pos && (inner == 0)) {
      if (left == 0) {
        translate([base_h,bracket_thk+1,bracket_len-bracket_thk] + [6.75,0,-38.5]) rotate([90,0,0]) cylinder(r=rivet_r, h=rivet_h+1);
        translate([base_h,bracket_thk+1,bracket_len-bracket_thk] + [19.75,0,-13.5]) rotate([90,0,0]) cylinder(r=rivet_r, h=rivet_h+1);
      } else {
        translate([base_h,bracket_thk+1,bracket_thk] + [6.75,0,38.5]) rotate([90,0,0]) cylinder(r=rivet_r, h=rivet_h+1);
        translate([base_h,bracket_thk+1,bracket_thk] + [19.75,0,13.5]) rotate([90,0,0]) cylinder(r=rivet_r, h=rivet_h+1);
      }
    }
  }
}


module main(part="rt") {
  if (part == "rt") {
    rotate([0,-90,0]) tower(0);
  } else if (part == "lt") {
    translate([0, 0, base_w]) rotate([0, 90, 0]) tower(1);
  } else if (part == "rtb") {
    rotate([0,-90,0]) union() {
      tower(0,rt_holes=false);
      translate([-bracket_thk,base_d,base_h]) rotate([0,90,-90]) bracket(0,0,holes=false);
    }
  } else if (part == "ltb") {  
    translate([0, 0, base_w]) rotate([0, 90, 0]) union() {
      tower(1,lt_holes=false);
      translate([base_w+bracket_thk,0,base_h]) rotate([0,90,90]) bracket(0,1,holes=false);
    }
  } else if (part == "orb") {
    rotate([90, 0, 0]) bracket(0,0);
  } else if (part == "irb") {
    rotate([90, 0, 0]) bracket(1,0);
  } else if (part == "olb") {
    rotate([90, 0, 0]) bracket(0,1);
  } else if (part == "ilb") {
    rotate([90, 0, 0]) bracket(1,1);
  } else if (part == "dbgr") {  // Debug right
    tower(0);
    # translate([base_w+bracket_thk,0,base_h]) rotate([90,90,180]) bracket(1,0);
    # translate([-bracket_thk,base_d,base_h]) rotate([90,90,0]) bracket(0,0);
  } else if (part == "dbgl") {
    tower(1);
    # translate([base_w+bracket_thk,0,base_h]) rotate([90,90,180]) bracket(0,1);
    # translate([-bracket_thk,base_d,base_h]) rotate([90,90,0]) bracket(1,1);
  } else if (part == "dbginset") {
    rotate([0,-90,0]) difference() {
      tower(0, false, false);
      translate([-1,-base_d-1,base_h/3]) cube([base_w+2,2*base_d+2,1.5*arm_length+2]);
      translate([-1,45-1,-1]) cube([base_w+2,base_d+2,arm_length+2]);
    }
  }
}

main(part);
