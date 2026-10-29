// [FL_INDEX: keywords="openscad, 3d_parametric, 2n2r5_Parametric_2_Piece_Interlocking_Spool_-_100__Printable, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: 2n2r5 Parametric 2 Piece Interlocking Spool - 100% Printable

// ===== file: spoolHubs.scad =====
include <write/write.scad>
use <utils/build_plate.scad>
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

Filename: spoolHubs.scad
Date of Creation: 7/9/13
True Revision Number: V1.14
Date of Revision: 7/14/13

Description:
This script will create custom reel hubs

Change Log:

V. 1.1 7/14/13

- Fixed Male Connector. It was not properly oriented and was only half the height that It should have been.


V. 1.1 7/11/13

- Made spool symmetrical so only 1 stl is needed to print spool.
- Fixed Teardrop shapes to auto populate and size
- Cleaned up variables (ready for thingiverse customizer)
- Changed defaults to make more people happy

Todo:
 
 - different hub patterns
 - Make clips generate automatically with size of spool (maybe, kind of like it how it is now)
 - Add "write.scad" so we can add text to non-teardrop cut sides

*/

	


/* [Reel Dimensions] */
//Outside Diameter of part that filament winds on (closest to sides)
hubMajorDiameter = 35; //[10:70]
//Outside Diameter of part that filament winds on (closest to center)
hubMajorDiameterCenter = 30; //[10:70]
//Inside Diameter of part that filament winds on (closest to sides)
hubMinorDiameter = 25; //[5:65]
//Outside Diameter of part that filament winds on (closest to center)
hubMinorDiameterCenter = 25; //[5:65]
//Reel Width (assumes that you print 2 at this size)
reelWidth = 150; //[40:200]
//Side of reel thickness
sideWallWidth = 2.5; //[1,1.5,2,2.5,3]
//Side Of reel height
sideWallHeight = 100; //[15:150]
/* [Interconnect Options] */
// Inter-connect Clip Count for each side (only counts extruded peices)
clipCount = 5; //[1:10]
// Height/Depth of clip interface (anything higher that 5 is pointless)
clipHeight = 3; //[1:10]
//Clip Width (3 is a good starting point)
clipWidth1 = 5; // [1:10]
// Used as spacer for interconnects from the sidewalls 
fineDetail = .5 ; 
/* [More Options] */
// Filament hole size (this variable is enlarged by 10%)
filamentSize = 1.75; // [1.75,2,3,3.5]
//Tear Drop Cutouts? (1 = yes , 0 = No)
teardropcut = 1; // [1:yes, 0:no]
// Quality of Round Edges (You may be waiting a while if your number is higher than 50)
fcy = 50; // [0:100]
//for display only, doesn't contribute to final object
build_plate_selector = 3; //[0:Replicator 2,1: Replicator,2:Thingomatic,3:Manual]

//when Build Plate Selector is set to "manual" this controls the build plate x dimension
build_plate_manual_x = 200; //[100:400]

//when Build Plate Selector is set to "manual" this controls the build plate y dimension
build_plate_manual_y = 200; //[100:400]

build_plate(build_plate_selector,build_plate_manual_x,build_plate_manual_y); 

/* *************** DO NOT CHANGE ANYTHING BELOW THIS LINE *************** */

/*  [Hidden]  */
/* --- Variable Conversion & Maths --- */
outHub = hubMajorDiameter;
outHubCenter = hubMajorDiameterCenter;
inHubBase = hubMinorDiameter;
inHubCenter = hubMinorDiameterCenter;
hh = reelWidth ;
cc = clipCount ;
inHubClip = (((outHubCenter-inHubCenter)/2+inHubCenter)/2) ;
teardropArea = ((sideWallHeight-outHub)/2 - sideWallWidth);
teardropBig = (teardropArea*.4);
teardropSmall = (teardropArea * .2);
// The following function gets the circumfrence of the middle of the teardrop area, divides that by the size of the diameter of the teardropbig diameter, subtracts -1 from that result and then rounds it off.
tdc = round(((((sideWallHeight- outHub)/4 + outHub/2) * 3.1459)/teardropBig )-1);
echo(tdc, "teardrop cutouts have been automatically been generated");
ff = tdc ; // 
clipWidth =  outHubCenter/2-inHubCenter/2-(2*fineDetail) ;
volumeCylinder = ((pow(sideWallHeight/2-sideWallWidth,2)*3.1459*hh))/1000 -  (pow(outHub/2,2)*3.1459*hh)/1000;

echo("Max Filament Volume is ", round(volumeCylinder)," cm³");
echo("Estimated Filament Weight is ",round(volumeCylinder*1.04)/1000, " kilograms");

// teardrop cutout module
module teardrop(){
color("transparent")
	if (teardropcut == 1) {
	
							for (fff=[0:ff]){							
						rotate([0,0,fff*360/ff])
							
								hull() {
									translate([0,(sideWallHeight/2 - teardropBig)-sideWallWidth,sideWallWidth/2])
									cylinder (r=teardropBig ,h=sideWallWidth, $fn=fcy, center=true);
								
									translate([0,(outHub/2 + teardropSmall) ,sideWallWidth/2])
									cylinder (r=teardropSmall,h=sideWallWidth, $fn=fcy, center=true);
								}
							
						}
	} else {

	}

}


module spoolConnectorFemale(){
	
		difference(){	
					color("firebrick")
					union(){
					
						cylinder(r=sideWallHeight/2,h=sideWallWidth, $fn=fcy);

						cylinder(r1=outHub/2, r2=outHubCenter/2, h=hh/2,$fn=fcy);


						//start material add for male connector
							rotate([0,0,(360/cc/2)]){
								
								for (ccc=[0:cc]){

								rotate([0,0,ccc*360/cc])
								translate([0,inHubClip,(hh/2)+clipHeight/2])
								cube([clipWidth1*.9,clipWidth*.9,(clipHeight+fineDetail)*.9],center=true);
								}
							}
					}
					color("transparent")
					union(){
						cylinder(r1=inHubBase/2,r2=inHubCenter/2, h=hh/2, $fn=fcy);

					//start material removal for female connector
							for (ccc=[0:cc]){

								rotate([0,0,ccc*360/cc])
								translate([0,inHubClip,(hh/2)-(clipHeight/2)-(fineDetail/2)])
								cube([clipWidth1,clipWidth,clipHeight+fineDetail],center=true);
						}
					//Make Spool Lighter
							//Tear Drop Shape cutouts
							teardrop();

					//Give a place to hook filament so we can wind it
						rotate([0,0,20])
						translate([0,outHub/2+sideWallWidth,sideWallWidth/2])
						cylinder(r=filamentSize/2*1.1, h=sideWallWidth, center=true, $fn=fcy);

						//Give a place to hook filament so we can hold it after winding
						rotate([0,0,20])
						translate([0,-(sideWallHeight/2-sideWallWidth),sideWallWidth/2])
						cylinder(r=filamentSize/2*1.1, h=sideWallWidth, center=true, $fn=fcy);



					}
		}
	
}



{

spoolConnectorFemale();
translate([sideWallHeight,0,0])
%spoolConnectorFemale();
}
