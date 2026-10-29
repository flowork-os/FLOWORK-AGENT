// [FL_INDEX: keywords="openscad, 3d_parametric, Parametric_Sixaxis_Phone_Clip, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Parametric Sixaxis Phone Clip

// Simple Sixaxis Phone or Tablet Holder
// (c) 2013, Christopher "ScribbleJ" Jansen


/* [SixAxis] */

// Thickness of the entire clip
six_clip_thick = 5;
// Width of entire clip
six_clip_w = 15.5;

// Thickness of Sixaxis Controller
six_clip_d = 26.5;
// Depth of clip on front side
six_clip_db = 15;
// Length of Sixaxis Controller
six_clip_l  = 49;
// Length of clip on top of Sixaxis
six_t_overlap = 10;

/* [Phone] */

// How far we cover the front of the phone
phone_clip_overlap = 5;
// Thickness of the phone
phone_clip_d = 18.5;
// Length or Width of the phone
phone_clip_l = 70;
// Angle of Phone to Sixaxis
phone_clip_ang = 30;
// Phone clip distance from Sixaxis
phone_clip_extra = 20;
// Where to attach the phone clip on Sixaxis clip
phone_clip_attach = six_clip_d;

rotate([90,0,0])
{
  color("green") six();
  translate([six_clip_l+six_clip_thick,0,phone_clip_attach]) rotate([0,-phone_clip_ang,0]) phone();
}


module phone()
{
  cube([phone_clip_l + phone_clip_extra + six_clip_thick, six_clip_w, six_clip_thick]);
  translate([phone_clip_extra-six_clip_thick,0,six_clip_thick]) phone_arm();
  translate([phone_clip_extra + phone_clip_l + six_clip_thick,0,six_clip_thick]) mirror([1,0,0]) phone_arm();

}
module phone_arm()
{
  cube([six_clip_thick, six_clip_w, phone_clip_d]);
  translate([0,0,phone_clip_d]) cube([six_clip_thick + phone_clip_overlap, six_clip_w, six_clip_thick]);
}

module six()
{
      // underside
      cube([six_clip_l, six_clip_w, six_clip_thick]);    
      // front
      translate([-six_clip_thick,0,0]) cube([six_clip_thick, six_clip_w, six_clip_thick + six_clip_db]);
      // back of sixaxis
      translate([six_clip_l,0,0]) cube([six_clip_thick, six_clip_w, six_clip_thick *2  + six_clip_d]);
      // top of sixaxis
      translate([six_clip_l - six_t_overlap,0,six_clip_thick + six_clip_d]) cube([six_t_overlap, six_clip_w, six_clip_thick]);
}