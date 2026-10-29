// [FL_INDEX: keywords="openscad, 3d_parametric, Clip-on_feet_for_play_yard_fence__North_States_Superyard, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Clip-on feet for play yard fence (North States Superyard)

len = 180; // non-test: 185; test: 90;
wid = 30; // non-test: 25 (was: 30); test: 7;
thk = 6;
gap = 7.4; // == 27.8 - 20.4 (between floor and bottom rail)

w = 13.9;  // bottom rail width
h = 27.8; // rail height + floor gap // 20.4 -> .7 fillet offset; 27.8 -> .6 fillet offset
h0 = 20.4;  // rail height
clip_thk=1.5;  // inset on each side (below rail, to keep foot tight onto rail)

bottom = false;  // experimental design

rad = 27.8;  // curvature; will need to change hardcoded offsets of top fillets if this changes (see TODO below)


$fn=72;

module fillet(r, h) {
  difference() {
    cube([h, r, r]);
    translate([-1, 0, 0]) rotate([0, 90, 0]) cylinder(h=h+2, r=r);
  }
}

module main() {
  // Ugly eqn warning (lazy approach to geometry: trig it to death :)
  ph = 0.5*acos((rad-h)/rad);
  y = h/tan(ph);
  l2 = 0.5*(len - w - 2*thk);

  union() {
    difference () {
      cube([wid, len, (bottom ? h0+gap+thk/4 : h+thk)]);
      // Rounded-off top (...)
      translate([-1, l2-y, thk+rad]) rotate([0, 90, 0]) cylinder(r = rad, h = wid+2);
      translate([-1, len-l2+y, thk+rad]) rotate([0, 90, 0]) cylinder(r = rad, h = wid+2);
      translate([-1, -1, thk]) cube([wid+2, l2-y+1, h+gap+1]);
      translate([-1, len-l2+y, thk]) cube([wid+2, l2-y+1, h+gap+1]);
      // Slot
      if (bottom) {
        translate([-1, l2+thk, gap]) cube([wid+2, w, h0]);
        translate([-1, l2+1.25*thk, gap+thk/2]) cube([wid+2, w-thk/2, h0]);
      } else {
        translate([-1, l2+thk, h-h0]) cube([wid+2, w, h0]);
        translate([-1, l2+thk+clip_thk, -1]) cube([wid+2, w-2*clip_thk, h0+1]);
      }
      // Base fillet
      translate([-1,thk/2-.1,thk/2+.1]) rotate([90,0,0]) fillet(h=wid+2,r=thk/2);
      translate([-1,len-thk/2+.1,thk/2+.1]) fillet(h=wid+2,r=thk/2);
      // Top fillet; TODO: parameterize 1.5/0.4 hardcoded offsets
      translate([-1,l2+0.75*thk-(bottom?1.5:.4),thk/4+(bottom ? h0+gap-0.75*thk : h)+.1]) rotate([90,0,0]) fillet(h=wid+2,r=0.75*thk);
      translate([-1,len-l2-0.75*thk+(bottom?1.5:.4),thk/4+(bottom ? h0+gap-0.75*thk : h)+.1]) fillet(h=wid+2,r=0.75*thk);
    }
  }
}

main();
