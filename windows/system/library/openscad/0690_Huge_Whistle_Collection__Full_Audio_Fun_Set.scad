// [FL_INDEX: keywords="openscad, 3d_parametric, Huge_Whistle_Collection__Full_Audio_Fun_Set, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Huge Whistle Collection (Full Audio Fun Set)


// Pfeife by Nischi, Alexander Nischelwitzer
// nischelwitzer@gmail.com (C)Jan/2013
// http://www.thingiverse.com/thing:41915
//
// V1.1 Rotationsrundung weg
// V1.2 stärkerer Halter
// V2.0 Optimierunge für Parameter
// V2.1 Textparameter, Anpassung Innenkugel hohl
// V2.2 Innenkugel mit 1mm Ständer 
// V2.3 dynamischer Halter (scale)
// V2.4 innenreifen für rad>40 zum deckel machen, innenkugel true/false
// V2.5 if statements, round text, dynamic handle, staender, adjustment inner sphere
// V2.6 corrected some bugs, better whistle hole
// V2.7 paramter version

use<write.scad>  // http://www.thingiverse.com/thing:16193

// ============================================================
// Paramters 

dicke  =   2;  // pfeife wandstärke [mind. 2]
breite =   6;  // breite blasschlitz 

ball   =   3;  // innenkugel (wandstärke auf 1 mm)
buffer =   0;  // für test (innenblick)
texth  =   1;  // texthoehe

// turn features on and off

dotext =   false; // do normal text
dortxt =   false;  // do round text
dohold =   flase;  // do holder
dostay =   false;  // do staender

// ============================================================
 
// whistel: text, textsize, rad, height, length, do sphere
//                           25      20      30

translate([0,  0.0,  0]) pfeife("", 0.0, 40, 15, 35, true);
translate([0,  5.0, 15]) pfeife("", 0.0, 30, 15, 30, true);
translate([0,  7.5, 30]) pfeife("", 0.0, 25, 15, 25, true);
translate([0, 10.0, 45]) pfeife("", 0.0, 20, 15, 20, true);

// ============================================================

module pfeife(name,sizename,rad,hoehe,laenge, doball)
{

  if (dohold) rotate([90,0,0]) translate([-rad/2+0.1,hoehe/2,0]) 
    scale([15/hoehe,1,1]) halter(hoehe);

  if (dotext) rotate([0,0,0])  translate([0,0,hoehe]) texter(name, sizename);
  if (dortxt) 
  {
    writecylinder(name,[0,0,0],t=3,h=8,font="letters.dxf", 
      space=1.0, rad/2+1,hoehe,face="top");
    // writecylinder("HDW",[0,0,0],t=3,h=9,font="letters.dxf", 
    //   space=1.2, rad/2, hoehe,face="top", ccw=true);
  }

  difference() 
  {
    union()  
    {       
      color([1,0,0,1]) translate([0,0,0]) cylinder(hoehe, r=rad/2, $fn = 35); 
      color("green") translate([0,rad/2-breite,0]) cube([laenge,breite,hoehe]);  
      color("green") translate([0,0,0]) cube([rad/2,rad/2,hoehe]); 
	}
    translate([0,0,dicke]) cylinder(hoehe-dicke*2+buffer, r=rad/2-dicke, $fn = 25); 
    translate([0,rad/2-breite+dicke,dicke]) 
      cube([laenge+dicke,breite-dicke*2,hoehe-dicke*2+buffer]);

    if (rad > 39) // stützkreis
      translate([0,0,0]) cylinder(hoehe, r=(rad-25)/2-dicke, $fn = 25); 
 
    translate([dicke*5,rad/2-dicke/3,dicke]) rotate([0,0,150])
      cube([dicke*5,dicke*2,hoehe-2*dicke]);  // Pfeifenschlitz mit Winkel
    translate([4,rad/2-7.5,dicke]) rotate([0,0,0])
      cube([rad/8,10,hoehe-2*dicke]); // Schlitz gerader Block
  }

  if (dostay) // to let it stay on table for presentation
    color("black") translate([-rad/6,-rad/2,0]) cube([rad/3,dicke,hoehe]); 

  if (rad > 39) // stützkreis
  {
    difference() {
      translate([0,0,dicke]) cylinder(hoehe-dicke*2, r=(rad-25)/2, $fn = 35);
      translate([0,0,dicke]) cylinder(hoehe-dicke*2, r=(rad-25)/2-dicke, $fn = 25); 
    }
  } 

  if (doball) // innere sphere - innenkugel mit stäender
  {
    color("red") translate([0,rad/2-7.5,dicke]) cylinder(1, r=1, $fn = 10);
    difference() // innenkugel
    {
      color("red") translate([0,rad/2-7.5,dicke+ball+1+1]) sphere(ball+1, $fn=25); 
      color("red") translate([0,rad/2-7.5,dicke+ball+1+1]) sphere(ball, $fn=25); 
    }
  }
}

// ============================================================

module texter(gotname="NIS", sizename=11)
{
  color([1,1,1])   translate([0.5,2,0]) rotate([0,0,40])
    write(gotname,t=3,h=sizename,font="letters.dxf", space=0.90, center=true);
}

module halter(hoehe)
{
  difference() 
  {
    union()  
    {       
      color("red") translate([0,0,-dicke]) cylinder(dicke*2, r=hoehe/2, $fn = 25); 
	}
    translate([0,0,-dicke]) cylinder(hoehe-dicke*2, r=hoehe/2-dicke*hoehe/15, $fn = 25); 
    translate([0,-hoehe,-dicke]) cube([hoehe,hoehe*2,dicke*2]); 
  }
}

// ============================================================

