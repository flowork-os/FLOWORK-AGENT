// [FL_INDEX: keywords="openscad, 3d_parametric, Bandage_Cage_for_Cat_Leg, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Bandage Cage for Cat Leg

inner_d   = 48;
inner_r   = inner_d/2;
inner_l   = 125;
leg_d     = 28;
leg_r     = leg_d/2;
thickness = 3;

huge = 500;

$fn=9;

module air_holes()
{
  // Air holes
  for(a = [0:120:240])
  {
    for(h = [0:thickness*4:(inner_l - (inner_r*2))])
    {
      translate([0,0,h])
      rotate([0,0,a])
      translate([-huge/2,-inner_r/2.5,0]) cube([huge, inner_r/1.25, thickness*2]);
    }
  }
}

difference()
{
rotate([0,90,0])
difference()
{
  union() 
  {
    cylinder(r=inner_r + thickness, h=inner_l - (inner_r*2));
    sphere(r=inner_r+thickness);
    translate([0,0,inner_l - (inner_r*2)]) sphere(r=inner_r+thickness);
  }

  air_holes();

  // Insides
  cylinder(r=inner_r, h=inner_l - (inner_r*2));
  sphere(r=inner_r);
  translate([0,0,inner_l - (inner_r*2)]) sphere(r=inner_r);

  // Leg hole
  cylinder(r=leg_r, h=huge);

  // Air holes
  //for(a = [0:120:360])
  //{
  //  rotate([0,0,a]) translate([0,0,(inner_l - (inner_r*2))/2])
  //    cube([thickness*2, huge, inner_l - (inner_r*2)], center=true);
  //}


}
translate([-huge/2,-huge/2,-huge]) cube([huge,huge,huge]);
}