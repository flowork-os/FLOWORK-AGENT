// [FL_INDEX: keywords="openscad, 3d_parametric, OpenSCAD_Threadless_Ballscrew_-_Highly_Customizable, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: OpenSCAD Threadless Ballscrew - Highly Customizable

use <write/Write.scad>
/*

This file had been created by Tim Chandler a.k.a. 2n2r5 and is
being shared under the creative commons - attribution license.
Any and all icons, references to 2n2r5.com, 2n2r5.net, Tim
Chandler ,2n2r5 or Trademarks must remain in the the end product.
This script is free to use for any and all purposes, both
commercial and non-commercial provided that the above conditions
are met.


Please refer to http://creativecommons.org/licenses/by/3.0/
for more information on this license.
*/

/*

Script by: Tim Chandler (2n2r5)

Filename: threadless_ball_screw.scad
Date of Creation: 7/26/13
True Revision Number: V1.121
Date of Revision: 7/30/13

Description:
This will create a customizable version of thing:112718, the "Threadless Ball Screw", for mounting on the solidoodle bed.


Todo:

 - make prettier bases that fit the platform better
 - add mounting solutions to fit more applications
 - make an adjustable tension system to combat fatigue
 - create a selectable library to choose from standard bearings


*/

/* [Global] */
//Show Text Summary
text = "true" ; //[true,false]

/* [Base Shape and Size] */

// Circle or Rectangle base (more options coming)
Base_Shape= "round"; // ["round":Round,"box":Box] 

//Height of Base (OEM M3 screws will stick out around 14-15mm)
Base_Height = 14;

//Bed Hole Size (This should be greater than the smooth rod diameter by enough that it doesn't inhibit the rod from turning)
Bed_Hole_Size = 9;


// -------------- "Box" Base Shape Options ---------- 

//Y width of Base
Box_Y_Width = 35;

//X width of Base
Box_X_Width = 35;

// -------------- "Round" Base Shape Option ---------

//Round Base width 
Round_Base_Width = 37;

/* [Mounting Options] */

//Which bed type? Other will only give a custom 4 hole option.
Solidoodle_Bed_Type = "aluminum" ; //[aluminum, wood, other]

// ---------------- "Other" Platform Options -----------

//Distance Between mounting holes on Y axis
Other_Bed_Mounting_Y = 25 ;

//Distance Between mounting holes on X axis
Other_Bed_Mounting_X = 15 ;

//Mounting screw size (M3 is standard)
Mount_Screw_Size = 3 ;// [3:M3,4:M4,5:M5]

//Bed mounting screw hole depth
Bed_Mounting_Hole_Depth = 14 ;




/* [Bearing & Smooth Rod Options] */

//Bearing Outer Diameter
Bearing_Outer_Diameter = 10 ;// [6:22]

//Bearing Inner Diameter and Screw hole size
Bearing_Inner_Diameter = 3 ; //[3,4,5,6]

//Bearing Width ;
Bearing_Width = 4 ; //[2,2.5,3,4,5,6]

//Total Number of Bearings (use 4 bearings works best with wood bed)
Number_of_Bearings = 4; //[2,3,4,5]

//Nut Size for screws that hold bearings (this should be the same as the Bearing ID)
Bearing_Nut_Size = 6.3; //[9:M5, 8:M4,6.3:M3]

//Screw Length
Screw_Length = 15;

//Smooth Rod Diameter
Smooth_Rod_Diameter = 8 ; //[9.525:3/8,7.9375:5/16,6.35:1/4,3:3MM,5:5MM,6:6MM,8:8MM,10:10MM,12:12MM]

//Use this to rotate the bearings if they are not in a friendly place
Bearing_Rotation_Adjustment = 52;

//How many MM per rotation? This is like thread pitch on threaded rod.
Bearing_Pitch = 5 ; 

//Use this to move the bearing in to create a tight fit
snug = .4; // [.05,.1,.15,.2,.25,.3,.35,.4]


//Tilt (Makes bearing tilt by X degrees inward or outward)
Bearing_Tilt = 0 ; //[-5:5]


//Reverse "Thread"?
Reverse_Thread = "no" ;//["yes":yes,"no":no]

/* ------------------- Rookie Line (Do not cross unless you know what you are doing) --------------------- */

/* [hidden] */

/* Variable Clean-up (makes pretty variables usable) */

BaseShape = Base_Shape	;
mss = Mount_Screw_Size	;
sdbt = Solidoodle_Bed_Type;
mhd = Bed_Mounting_Hole_Depth;
bh = Base_Height		;
bhs = Bed_Hole_Size		;
byw = Box_Y_Width		;
bxw = Box_X_Width		;
bwr = Round_Base_Width	;
bod = Bearing_Outer_Diameter;
bid = Bearing_Inner_Diameter;
bw = Bearing_Width		;
nob = Number_of_Bearings;
bnd = Bearing_Nut_Size	;
srd = Smooth_Rod_Diameter;
rotAdj = Bearing_Rotation_Adjustment;
pitch = Bearing_Pitch	;
obmx = Other_Bed_Mounting_X/2 ;
obmy = Other_Bed_Mounting_Y/2;
rt = Reverse_Thread;
bt = Bearing_Tilt		;
sl = Screw_Length		;
//Mounting holes 
mhfc = [[ -12.5,7.5,-(bh-mhd)/2 ],[ -12.5,-7.5,-(bh-mhd)/2 ],[ 12.5,7.5,-(bh-mhd)/2],[12.5,-7.5,-(bh-mhd)/2 ]] ; 						

// [[ -12.5,7.5,-(bh-mhd)/2 ],[ -12.5,-7.5,-(bh-mhd)/2 ],[ 12.5,7.5,-(bh-mhd)/2 ],[12.5,-7.5,-(bh-mhd)/2 ]]   <--Use this for Aluminum Bed
mhfcw = [[ -8,8,-(bh-mhd)/2 ],[ -8,-8,-(bh-mhd)/2 ],[ 8,8,-(bh-mhd)/2 ],[8,-8,-(bh-mhd)/2 ]]; // <-- Use this for Wood Bed 

//Mounting holes for bed type not Solidoodle
mhfco = [[ -obmx,obmy,-(bh-mhd)/2 ],[ -obmx,-obmy,-(bh-mhd)/2 ],[ obmx,obmy,-(bh-mhd)/2 ],[obmx,-obmy,-(bh-mhd)/2 ]]; // This defines the "other" bed type option

//simplify base size
base = [bxw,byw,bh];

//simplify bearing
bsize = [bod/2,bid/2,bw];

//bearing mounting angle to get desired pitch
bma = round(atan(pitch / (srd * 3.141592 ))*10)/10; //Use round(var*10)/10 to round the angle down to the nearest 10th

//X distance from center of bearing
bdfc = cos(bma)*(bod/2);

$fn=30;



echo (str("The bearing angle will be set to ", bma ," degrees."));
angleNotify = str("Bearing Angle = ", bma ," degrees");
pitchNotify = str("Pitch = ", pitch ," MM Per Rotation");
bearingSize = str("Bearing Dimensions = ",bid,":",bod,":",bw);
rtNotify = str("Reverse Thread?  ", rt );
//echo ("Bearing is " , bdfc , "Horizontally from edge.");
echo (snug);





				/* ------------- End Variables and Start Shapes Below ---------------*/

/*

			In the interest of making this script easily adaptable,
			all main shapes will be separate modules will be put
			together at the bottom of this script.

*/
/* --- This is the on-screen info Graphic since there is no option for Echo output in customizer --- */
if (text=="true"){
%color("red")
rotate([10,0,-140]){
translate([0,30,3])
rotate ([90,0,180]){
write(angleNotify,h=2,t=1,font="write/orbitron.dxf",center=true);
translate([0,3,0])
write(pitchNotify,h=2,t=1,font="write/orbitron.dxf",center=true);
translate([0,6,0])
write(bearingSize,h=2,t=1,font="write/orbitron.dxf",center=true);
translate([0,-3,0])
write(rtNotify,h=2,t=1,font="write/orbitron.dxf",center=true);
}
} } else {

}


// This builds the basic shape of the bearing For refrence and cutouts
module Bearing (bigd,smalld,bbwidth) {
	difference(){
		cylinder(r=bigd,h=bbwidth);
		%cylinder(r=smalld,h=bbwidth);
	}
}

//Main body of the nut.This acts as the Adapter between the bearing mounts and the bed mounts
module Base(){
	difference(){

		union(){
			if(BaseShape=="round"){
				cylinder(r=bwr/2,h=bh,center=true);
			} else if (BaseShape=="box"){
				cube(base,center=true);
			} else if (BaseShape=="yourShapeHere"){
				//More shapes can be added here
			}
		}

		union(){

			//Start mounting screw cutouts here
			if (sdbt=="aluminum") {
				for(i=mhfc) {
					translate(i) {
						cylinder(r=mss/2, h=mhd, center=true);
					}		
				}
			} else if (sdbt=="wood") {
				for(g=mhfcw) {
					translate(g) {
						cylinder(r=mss/2, h=mhd, center=true);
					}		
				}
			} else if (sdbt=="other") { //This is where the "other" bed type mounting screw cutouts are.
				for(h=mhfco) {
					translate(h) {
						cylinder(r=mss/2, h=mhd, center=true);
					}
				}
			}
			//Hole for smooth rod
			%cylinder(r=(srd/2)*1.0,h=100,center=true); //This shows the smooth rod that the bearings will be spaced for.
			cylinder(r=bhs/2, h=bh,center=true );  //This is the actual hole cut.

		}
	}
}


/* Bearing mounts are all made positive and will be subtracted from base */
module bearingMounts(){
	
// --------------- ***** For anything that will be used in a rotational translate loop (I.E. bearing cut out, mounting screw, mounting nut) ****** ----------- //
	for (j= [0:nob]) {
		if (rt=="yes") { //"Reverse Thread" option
			rotate([-bma,bt,j*360/nob+rotAdj]) translate([(srd/2)+bdfc-snug,0,bh/2-1]){  //snug is used to apply force between the bearing and the smooth rod
		
			#Bearing(bod/2*(1.05),bid/2,bw*(1.05)); //Main Bearings as defined in bearing module plus 5% to keep slack around the bearing
			translate([0,0,-bh/2])cylinder(r=bid/2,h=bh,center=true); //Shaft for bolt/screw to hold the bearing
			translate([0,0,-bh+bnd/3])cylinder(r=bnd/2,h=bh/2,$fn=6,center=true); //Retainer for nut bearing bolt
		}
		}  else if (rt=="no") { //"Regular Thread" option
			rotate([bma,bt,j*360/nob+rotAdj]) translate([(srd/2)+bdfc-snug,0,bh/2-1]){ 

					#Bearing(bod/2*(1.05),bid/2,bw*(1.05)); //Main Bearings as defined in bearing module plus 5% to keep slack around the bearing
					translate([0,0,-bh/2])cylinder(r=bid/2,h=bh,center=true); //Shaft for bolt/screw to hold the bearing
					#translate([0,0,bnd*.55-sl])cylinder(r=bnd/2,h=2*(bnd*.55),$fn=6,center=true); //Retainer for nut bearing bolt


			}
		}
	}

}

// Part assembly starts here
difference(){
Base();
bearingMounts();
}
