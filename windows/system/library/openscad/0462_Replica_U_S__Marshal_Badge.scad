// [FL_INDEX: keywords="openscad, 3d_parametric, Replica_U_S__Marshal_Badge, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Replica U.S. Marshal Badge

// Marshal badge:
use <write/Write.scad>;

TopText="U.S.";
BottomText="MARSHAL";
$fn=60;

/* [Hidden] */
BADGE_DIAMETER=25.4*1.5; //mm
BADGE_HEIGHT=4.5; //mm
RING_OUTER_DIAMETER=1.2; //percentage
RING_INNER_DIAMETER=0.9; //percentage
RING_OFFSET=0; //mm

module star_5_point(radius=10){
 polygon(points=[
  from_polar(radius, 0),
  from_polar(radius, 72),
  from_polar(radius, 72*2),
  from_polar(radius, 72*3),
  from_polar(radius, 72*4)],
  paths=[[0,2,4,1,3]]);
}

function from_polar(r=1,theta=60) = [r*cos(theta),r*sin(theta)];
rotate([0,0,-90]){
intersection(){
 //star
 rotate([0,0,180]) linear_extrude(height=BADGE_HEIGHT) star_5_point(BADGE_DIAMETER/2);

 translate([0,0,-2*BADGE_DIAMETER+BADGE_HEIGHT]) rotate([0,90,0]) sphere(r=BADGE_DIAMETER*2);
}
difference(){
 intersection(){
  //ring
  difference(){
   cylinder(r=BADGE_DIAMETER/2*RING_OUTER_DIAMETER,h=BADGE_HEIGHT);
   cylinder(r=BADGE_DIAMETER/2*RING_INNER_DIAMETER, h=BADGE_HEIGHT);
  }
  translate([0,0,-2*BADGE_DIAMETER+BADGE_HEIGHT+RING_OFFSET]) sphere(r=BADGE_DIAMETER*2);
 }

 rotate([0,0,90]) scale([1,1,BADGE_HEIGHT*2]) writecylinder(BottomText,[0,0,0],(BADGE_DIAMETER*RING_OUTER_DIAMETER)/2+1,0,face="top",ccw=true);
 rotate([0,0,90]) scale([1,1,BADGE_HEIGHT*2]) writecylinder(TopText,[0,0,0],(BADGE_DIAMETER*RING_OUTER_DIAMETER)/2+1,0,face="top",ccw=false);
}

intersection(){
 translate([0,0,-1])
  intersection(){
   //ring
   difference(){
    cylinder(r=BADGE_DIAMETER/2*RING_OUTER_DIAMETER,h=BADGE_HEIGHT);
    cylinder(r=BADGE_DIAMETER/2*RING_INNER_DIAMETER, h=BADGE_HEIGHT);
   }
   translate([0,0,-2*BADGE_DIAMETER+BADGE_HEIGHT+RING_OFFSET]) sphere(r=BADGE_DIAMETER*2);
  }
translate([-BADGE_DIAMETER*0.6, -BADGE_DIAMETER*0.6]) cube(BADGE_DIAMETER*1.2);
}
}