// [FL_INDEX: keywords="openscad, 3d_parametric, Updated__Parametric_Replicator_Spool_Holder, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Updated: Parametric Replicator Spool Holder

// ===== file: ReplicatorSpoolHolder_V2.0.scad =====
/* Uses OpenSCAD 2012.04.04

Parametric Replicator Spool Holder
==================================

This program renders 2 parts which allow for the mounting of non-standard spools on the Makerbot Replicator.

Part 1 is a left hand side wall support panel which clips into either of the holes at the back of the replicator which are
designed to be used by the Makerbot provided spool holders.  The panel design allows for larger spools to be offset from 
the standard spool holder by moving Part 2 along the slot.

Part 2 is a mounting tube and base which slides into the wall support panel and allows for the mounting of
the spool.

Both Part 1 and 2 can be customised for spools by changing the value of variables below.

The main variables which need to be customised are:

	SpoolHoleDiameter
	SpoolDepth

The "Layout" variable can be set to "Both", "Wall" or "Spool" to render the parts required for printing.

The Part 1 wall support panel can be Mirrored in ReplicatorG or Makerware to print for the right hand side spool.

*/

/* [Global] */

// What to you want to print?
part = "Both";										//  [Both:Both, Wall:Wall, Spool:Spool]

//--  Spool Dimensions     <<<<<<<=======   CHANGE THESE TO SUIT YOUR SPOOL.

// SpoolHoleDiameter = 52.0;								// Settings for standard Makerbot Spools.
// SpoolDepth = 80.0;
// SpoolHoleDiameter = 28.25;								// Settings for my PLA Spools.
// SpoolDepth = 76.0;


// Diameter of Hole in Centre of Spool (52.0 for Makerbot)?
SpoolHoleDiameter = 52.0;								// Settings for Makerbot Spools.

// Width of Spool (80.0 for Makerbot)?
SpoolDepth = 80.0;

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////

print_part();

module print_part() {
	if (part == "Both") {
		WallSupport();
		SpoolSupport();
	} else if (part == "Wall") {
		WallSupport();
	} else {
		SpoolSupport();
	}
}

/*
=========== Rounded Top Box based on thing:6400
=========== Thanks to IHeartRobotics
*/

module RoundTopBox(pad, box_l, box_w, box_h, round_r, smooth)
{

//  NOTE: This box has a flat bottom unlike thing:6400
//  ====

//  pad 	     	// Padding to maintain manifold
//  box_l			// Length
//  box_w 		// Width
//  box_h			// Height
//  round_		// Radius of round
//  smooth		// Number of facets of rounding cylinder

// To fix the corners cut the main cube with smaller cubes with spheres removed.

  difference() {
	cube([box_l, box_w, box_h], center = true);

	translate([0, -box_w/2+round_r, box_h/2-round_r]) {
		difference() {
			translate([0,-round_r-pad,round_r+pad])
				cube([box_l+2*pad, round_r*2+pad, round_r*2+pad], center = true);
			rotate(a=[0,90,0])
				cylinder(box_l+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}
	translate([0, box_w/2-round_r, box_h/2-round_r]) {
		difference() {
			translate([0,round_r+pad,round_r+pad])
				cube([box_l+2*pad, round_r*2+pad, round_r*2+pad], center = true);
			rotate(a=[0,90,0])
				cylinder(box_l+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}

// ----

	translate([-box_l/2+round_r, box_w/2-round_r, 0]) {
		difference() {
			translate([-round_r-pad,round_r+pad,0])
				cube([round_r*2+pad, round_r*2+pad, box_h+2*pad], center = true);
			cylinder(box_h+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}
	translate([box_l/2-round_r, box_w/2-round_r, 0]) {
		difference() {
			translate([round_r+pad,round_r+pad,0])
				cube([round_r*2+pad, round_r*2+pad, box_h+2*pad], center = true);
			cylinder(box_h+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}

	translate([-box_l/2+round_r, -box_w/2+round_r, 0]) {
		difference() {
			translate([-round_r-pad,-round_r-pad,0])
				cube([round_r*2+pad, round_r*2+pad, box_h+2*pad], center = true);
			cylinder(box_h+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}
	translate([box_l/2-round_r, -box_w/2+round_r, 0]) {
		difference() {
			translate([round_r+pad,-round_r-pad,0])
				cube([round_r*2+pad, round_r*2+pad, box_h+2*pad], center = true);
			cylinder(box_h+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}

// ----

	translate([-box_l/2+round_r, 0, box_h/2-round_r]) {
		difference() {
			translate([-round_r-pad, 0, round_r+pad])
				cube([round_r*2+pad, box_w+2*pad, round_r*2+pad], center = true);
			rotate(a=[0,90,90])
				cylinder(box_w+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}
	translate([box_l/2-round_r, 0, box_h/2-round_r]) {
		difference() {
			translate([round_r+pad, 0, round_r+pad])
				cube([round_r*2+pad, box_w+2*pad, round_r*2+pad], center = true);
			rotate(a=[0,90,90])
				cylinder(box_w+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}

// ----

	translate([box_l/2-round_r, box_w/2-round_r, box_h/2-round_r]) {
		difference() {
			translate([round_r+pad, round_r+pad, round_r+pad])
				cube([round_r*2+pad, round_r*2+pad, round_r*2+pad], center = true);
			sphere(round_r,center=true,$fn=smooth);
		}
	}
	translate([-box_l/2+round_r, box_w/2-round_r, box_h/2-round_r]) {
		difference() {
			translate([-round_r-pad, round_r+pad, round_r+pad])
				cube([round_r*2+pad, round_r*2+pad, round_r*2+pad], center = true);
			sphere(round_r,center=true,$fn=smooth);
		}
	}
	translate([box_l/2-round_r, -box_w/2+round_r, box_h/2-round_r]) {
		difference() {
			translate([round_r+pad, -round_r-pad, round_r+pad])
				cube([round_r*2+pad, round_r*2+pad, round_r*2+pad], center = true);
			sphere(round_r,center=true,$fn=smooth);
		}
	}
	translate([-box_l/2+round_r, -box_w/2+round_r, box_h/2-round_r]) {
		difference() {
			translate([-round_r-pad, -round_r-pad, round_r+pad])
				cube([round_r*2+pad, round_r*2+pad, round_r*2+pad], center = true);
			sphere(round_r,center=true,$fn=smooth);
		}
	}
}

}


/*
===========  OpenSCAD Shapes Library (www.openscad.at)
===========  Copyright (C) 2009  Catarina Mota <clifford@clifford.at>
*/


module tube(height, radius, wall) {
	difference(){
		cylinder(height, radius, radius,$fa=1);
		cylinder(height, radius-wall, radius-wall);
	}
}

module box(w,h,d) {
	scale ([w,h,d]) cube(1, true);
}

//-----------------------
//MOVES THE ROTATION AXIS OF A BOX FROM ITS CENTER TO THE BOTTOM LEFT CORNER
module dislocateBox(w,h,d){
	translate([w/2,h,0]){
		difference(){
			box(w, h*2, d+1);
			translate([-w,0,0]) box(w, h*2, d+1);
		}
	}
}


module rightTriangle(adjacent, opposite, depth) {
	difference(){
		translate([-adjacent/2,opposite/2,0]) box(adjacent, opposite, depth);
		translate([-adjacent,0,0]){
			rotate([0,0,atan(opposite/adjacent)]) dislocateBox(adjacent*2, opposite, depth);
		}
	}
}
/*
  ==============================================================================
   MAIN CODE
  ==============================================================================
*/


//--  Variables for Hole in Wall.

HoleInWallWidth = 32.0 * 1;									// Size of the hole in the Replicator Wall.
HoleInWallHeight = 17.0 * 1;
HoleInWallDepth = 5.0 * 1;
LedgeHeight = 10.0 * 1;										// Height of inside support ledge.
InsideSupportThickness = 3.0 * 1;								// Thickness of Cube to hold inside Replicator.

//--  Standard Build Variables.

OutsideBaseWidth = 80.0 * 1;									// Size of external support baseplate
OutsideBaseDepth = 4.0 * 1;
SideTrackWidth = 3.0 * 1;
SideTrackHeight = 5.0 * 1;
SideTopHeight = 6.0 * 1;
InnerTrackWidth = 3.0 * 1;
TubeThickness = 4.0 * 1;
TubeCollarWidth = 5.0 * 1;
TubeCollarHeight = 2.0 * 1;
TubeBaseClearance = 3.0 * 1;									// Space between edge of baseplate and tube.
TubeBaseSlippage = 0.5 * 1;									// Slippage between tube base plate and side rail.


//--  Calculated Dimensions

OutsideBaseHeight = SpoolHoleDiameter + (TubeBaseClearance * 2) + (SideTrackWidth * 2) + (TubeBaseSlippage * 2);

SideTrackStart = InsideSupportThickness + HoleInWallDepth + OutsideBaseDepth;
SideTopStart = SideTrackStart + SideTrackHeight;
SideTopWidth = SideTrackWidth + InnerTrackWidth;
UpperTrackStart = OutsideBaseHeight - SideTrackWidth;
UpperTopStart = OutsideBaseHeight - SideTopWidth;

SpoolPrintOffset = 30 * 1;									// Offset of Spool from Wall Support for print layout

SpoolBaseplateDepth = SideTrackHeight - 0.4;
SpoolBaseplateXorY = SpoolHoleDiameter + (TubeBaseClearance * 2);

//-- Wall Support Panel.

module WallSupport() {

//-- Inside Base with holding ledge.

  color("Aqua") translate([0, (LedgeHeight * -1),0])
		 cube([InsideSupportThickness, (HoleInWallHeight + LedgeHeight), HoleInWallWidth]);

//-- Hole in Wall Filler.

  color("CadetBlue") translate([InsideSupportThickness,0,0])
		 cube([HoleInWallDepth,HoleInWallHeight,HoleInWallWidth]);

//-- Outside Base.

  color("RoyalBlue") translate([(InsideSupportThickness + HoleInWallDepth),0,0])
		 cube([OutsideBaseDepth,OutsideBaseHeight,OutsideBaseWidth]);

//-- Bottom Side.

  color("Gray") translate([SideTrackStart,0,0])
		 cube([SideTrackHeight,SideTrackWidth,OutsideBaseWidth]);

//-- Top Side.

  color("Beige") translate([SideTrackStart,UpperTrackStart,0])
		 cube([SideTopHeight,SideTrackWidth,OutsideBaseWidth]);

//-- Lower Top Guide.

  color("LawnGreen") translate([SideTopStart + (SideTopHeight/2.0),SideTopWidth/2.0,OutsideBaseWidth/2.0]) rotate([90,90,90])
		 RoundTopBox( 0.1, OutsideBaseWidth, SideTopHeight, SideTopWidth,  1.5, 20);

//-- Upper Top Guide.

  color("LimeGreen") translate([SideTopStart+ (SideTopHeight/2.0),UpperTopStart + SideTopWidth/2.0,OutsideBaseWidth/2.0])
		 rotate([90,90,90])
		 RoundTopBox( 0.1, OutsideBaseWidth, SideTopHeight, SideTopWidth,  1.5, 20.0);

}

module BasePlate() {

	color("red") translate([SpoolPrintOffset, SideTrackWidth, 0])
	cube([SpoolBaseplateXorY,SpoolBaseplateXorY,SpoolBaseplateDepth]);
  
}

module MainTube() {
	
 	difference(){ 
	
    	color("Yellow") 
		translate([SpoolPrintOffset + (SpoolBaseplateXorY /2.0),SideTrackWidth + (SpoolBaseplateXorY / 2.0),SpoolBaseplateDepth-0.01])
		tube(SpoolDepth + SideTopHeight + 1.0,SpoolHoleDiameter/2.0,TubeThickness);
		
		color("Orange") 
		//  Leave 15mm lower collar to strengthen printing.
    	translate([SpoolPrintOffset,0,15])
		cube([SpoolBaseplateXorY,(SpoolBaseplateXorY  + TubeBaseClearance)/2,SpoolDepth  + SideTopHeight + 1.0 + TubeCollarWidth ]);
  }
}

module UpperCollar() {

	difference(){ 
    	color("SkyBlue")
 		translate([SpoolPrintOffset + (SpoolBaseplateXorY /2.0),SideTrackWidth + (SpoolBaseplateXorY / 2.0),SpoolDepth  + SideTopHeight + 1.0])
		tube(TubeCollarWidth,(SpoolHoleDiameter + TubeCollarHeight)/2.0,TubeCollarHeight);
		
    	translate([SpoolPrintOffset,0,0])
		cube([SpoolBaseplateXorY,(SpoolBaseplateXorY  + TubeBaseClearance)/2,SpoolDepth + SideTopHeight + 1.0 +TubeCollarWidth]);
  }
}

module SupportTriangle() {

	color("pink")
	translate([SpoolPrintOffset + (SpoolHoleDiameter /2.0)
			+ TubeBaseClearance,SpoolBaseplateXorY - TubeBaseClearance,SpoolBaseplateDepth-0.01]) rotate ([0,90,180])
	rightTriangle(SpoolDepth,SpoolHoleDiameter - TubeBaseClearance,TubeThickness);

}

//--	Spool Tube and support base.

module SpoolSupport() {

	BasePlate();
	MainTube();
	UpperCollar();
	SupportTriangle();
}

// ===== file: ReplicatorSpoolHolder_V2.0_scad.scad =====
/* Uses OpenSCAD 2012.04.04

Parametric Replicator Spool Holder
==================================

This program renders 2 parts which allow for the mounting of non-standard spools on the Makerbot Replicator.

Part 1 is a left hand side wall support panel which clips into either of the holes at the back of the replicator which are
designed to be used by the Makerbot provided spool holders.  The panel design allows for larger spools to be offset from 
the standard spool holder by moving Part 2 along the slot.

Part 2 is a mounting tube and base which slides into the wall support panel and allows for the mounting of
the spool.

Both Part 1 and 2 can be customised for spools by changing the value of variables below.

The main variables which need to be customised are:

	SpoolHoleDiameter
	SpoolDepth

The "Layout" variable can be set to "Both", "Wall" or "Spool" to render the parts required for printing.

The Part 1 wall support panel can be Mirrored in ReplicatorG or Makerware to print for the right hand side spool.

*/

/* [Global] */

// What to you want to print?
part = "Both";										//  [Both:Both, Wall:Wall, Spool:Spool]

//--  Spool Dimensions     <<<<<<<=======   CHANGE THESE TO SUIT YOUR SPOOL.

// SpoolHoleDiameter = 52.0;								// Settings for standard Makerbot Spools.
// SpoolDepth = 80.0;
// SpoolHoleDiameter = 28.25;								// Settings for my PLA Spools.
// SpoolDepth = 76.0;


// Diameter of Hole in Centre of Spool (52.0 for Makerbot)?
SpoolHoleDiameter = 52.0;								// Settings for Makerbot Spools.

// Width of Spool (80.0 for Makerbot)?
SpoolDepth = 80.0;

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////

print_part();

module print_part() {
	if (part == "Both") {
		WallSupport();
		SpoolSupport();
	} else if (part == "Wall") {
		WallSupport();
	} else {
		SpoolSupport();
	}
}

/*
=========== Rounded Top Box based on thing:6400
=========== Thanks to IHeartRobotics
*/

module RoundTopBox(pad, box_l, box_w, box_h, round_r, smooth)
{

//  NOTE: This box has a flat bottom unlike thing:6400
//  ====

//  pad 	     	// Padding to maintain manifold
//  box_l			// Length
//  box_w 		// Width
//  box_h			// Height
//  round_		// Radius of round
//  smooth		// Number of facets of rounding cylinder

// To fix the corners cut the main cube with smaller cubes with spheres removed.

  difference() {
	cube([box_l, box_w, box_h], center = true);

	translate([0, -box_w/2+round_r, box_h/2-round_r]) {
		difference() {
			translate([0,-round_r-pad,round_r+pad])
				cube([box_l+2*pad, round_r*2+pad, round_r*2+pad], center = true);
			rotate(a=[0,90,0])
				cylinder(box_l+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}
	translate([0, box_w/2-round_r, box_h/2-round_r]) {
		difference() {
			translate([0,round_r+pad,round_r+pad])
				cube([box_l+2*pad, round_r*2+pad, round_r*2+pad], center = true);
			rotate(a=[0,90,0])
				cylinder(box_l+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}

// ----

	translate([-box_l/2+round_r, box_w/2-round_r, 0]) {
		difference() {
			translate([-round_r-pad,round_r+pad,0])
				cube([round_r*2+pad, round_r*2+pad, box_h+2*pad], center = true);
			cylinder(box_h+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}
	translate([box_l/2-round_r, box_w/2-round_r, 0]) {
		difference() {
			translate([round_r+pad,round_r+pad,0])
				cube([round_r*2+pad, round_r*2+pad, box_h+2*pad], center = true);
			cylinder(box_h+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}

	translate([-box_l/2+round_r, -box_w/2+round_r, 0]) {
		difference() {
			translate([-round_r-pad,-round_r-pad,0])
				cube([round_r*2+pad, round_r*2+pad, box_h+2*pad], center = true);
			cylinder(box_h+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}
	translate([box_l/2-round_r, -box_w/2+round_r, 0]) {
		difference() {
			translate([round_r+pad,-round_r-pad,0])
				cube([round_r*2+pad, round_r*2+pad, box_h+2*pad], center = true);
			cylinder(box_h+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}

// ----

	translate([-box_l/2+round_r, 0, box_h/2-round_r]) {
		difference() {
			translate([-round_r-pad, 0, round_r+pad])
				cube([round_r*2+pad, box_w+2*pad, round_r*2+pad], center = true);
			rotate(a=[0,90,90])
				cylinder(box_w+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}
	translate([box_l/2-round_r, 0, box_h/2-round_r]) {
		difference() {
			translate([round_r+pad, 0, round_r+pad])
				cube([round_r*2+pad, box_w+2*pad, round_r*2+pad], center = true);
			rotate(a=[0,90,90])
				cylinder(box_w+4*pad,round_r,round_r,center=true,$fn=smooth);
		}
	}

// ----

	translate([box_l/2-round_r, box_w/2-round_r, box_h/2-round_r]) {
		difference() {
			translate([round_r+pad, round_r+pad, round_r+pad])
				cube([round_r*2+pad, round_r*2+pad, round_r*2+pad], center = true);
			sphere(round_r,center=true,$fn=smooth);
		}
	}
	translate([-box_l/2+round_r, box_w/2-round_r, box_h/2-round_r]) {
		difference() {
			translate([-round_r-pad, round_r+pad, round_r+pad])
				cube([round_r*2+pad, round_r*2+pad, round_r*2+pad], center = true);
			sphere(round_r,center=true,$fn=smooth);
		}
	}
	translate([box_l/2-round_r, -box_w/2+round_r, box_h/2-round_r]) {
		difference() {
			translate([round_r+pad, -round_r-pad, round_r+pad])
				cube([round_r*2+pad, round_r*2+pad, round_r*2+pad], center = true);
			sphere(round_r,center=true,$fn=smooth);
		}
	}
	translate([-box_l/2+round_r, -box_w/2+round_r, box_h/2-round_r]) {
		difference() {
			translate([-round_r-pad, -round_r-pad, round_r+pad])
				cube([round_r*2+pad, round_r*2+pad, round_r*2+pad], center = true);
			sphere(round_r,center=true,$fn=smooth);
		}
	}
}

}


/*
===========  OpenSCAD Shapes Library (www.openscad.at)
===========  Copyright (C) 2009  Catarina Mota <clifford@clifford.at>
*/


module tube(height, radius, wall) {
	difference(){
		cylinder(height, radius, radius,$fa=1);
		cylinder(height, radius-wall, radius-wall);
	}
}

module box(w,h,d) {
	scale ([w,h,d]) cube(1, true);
}

//-----------------------
//MOVES THE ROTATION AXIS OF A BOX FROM ITS CENTER TO THE BOTTOM LEFT CORNER
module dislocateBox(w,h,d){
	translate([w/2,h,0]){
		difference(){
			box(w, h*2, d+1);
			translate([-w,0,0]) box(w, h*2, d+1);
		}
	}
}


module rightTriangle(adjacent, opposite, depth) {
	difference(){
		translate([-adjacent/2,opposite/2,0]) box(adjacent, opposite, depth);
		translate([-adjacent,0,0]){
			rotate([0,0,atan(opposite/adjacent)]) dislocateBox(adjacent*2, opposite, depth);
		}
	}
}
/*
  ==============================================================================
   MAIN CODE
  ==============================================================================
*/


//--  Variables for Hole in Wall.

HoleInWallWidth = 32.0 * 1;									// Size of the hole in the Replicator Wall.
HoleInWallHeight = 17.0 * 1;
HoleInWallDepth = 5.0 * 1;
LedgeHeight = 10.0 * 1;										// Height of inside support ledge.
InsideSupportThickness = 3.0 * 1;								// Thickness of Cube to hold inside Replicator.

//--  Standard Build Variables.

OutsideBaseWidth = 80.0 * 1;									// Size of external support baseplate
OutsideBaseDepth = 4.0 * 1;
SideTrackWidth = 3.0 * 1;
SideTrackHeight = 5.0 * 1;
SideTopHeight = 6.0 * 1;
InnerTrackWidth = 3.0 * 1;
TubeThickness = 4.0 * 1;
TubeCollarWidth = 5.0 * 1;
TubeCollarHeight = 2.0 * 1;
TubeBaseClearance = 3.0 * 1;									// Space between edge of baseplate and tube.
TubeBaseSlippage = 0.5 * 1;									// Slippage between tube base plate and side rail.


//--  Calculated Dimensions

OutsideBaseHeight = SpoolHoleDiameter + (TubeBaseClearance * 2) + (SideTrackWidth * 2) + (TubeBaseSlippage * 2);

SideTrackStart = InsideSupportThickness + HoleInWallDepth + OutsideBaseDepth;
SideTopStart = SideTrackStart + SideTrackHeight;
SideTopWidth = SideTrackWidth + InnerTrackWidth;
UpperTrackStart = OutsideBaseHeight - SideTrackWidth;
UpperTopStart = OutsideBaseHeight - SideTopWidth;

SpoolPrintOffset = 30 * 1;									// Offset of Spool from Wall Support for print layout

SpoolBaseplateDepth = SideTrackHeight - 0.4;
SpoolBaseplateXorY = SpoolHoleDiameter + (TubeBaseClearance * 2);

//-- Wall Support Panel.

module WallSupport() {

//-- Inside Base with holding ledge.

  color("Aqua") translate([0, (LedgeHeight * -1),0])
		 cube([InsideSupportThickness, (HoleInWallHeight + LedgeHeight), HoleInWallWidth]);

//-- Hole in Wall Filler.

  color("CadetBlue") translate([InsideSupportThickness,0,0])
		 cube([HoleInWallDepth,HoleInWallHeight,HoleInWallWidth]);

//-- Outside Base.

  color("RoyalBlue") translate([(InsideSupportThickness + HoleInWallDepth),0,0])
		 cube([OutsideBaseDepth,OutsideBaseHeight,OutsideBaseWidth]);

//-- Bottom Side.

  color("Gray") translate([SideTrackStart,0,0])
		 cube([SideTrackHeight,SideTrackWidth,OutsideBaseWidth]);

//-- Top Side.

  color("Beige") translate([SideTrackStart,UpperTrackStart,0])
		 cube([SideTopHeight,SideTrackWidth,OutsideBaseWidth]);

//-- Lower Top Guide.

  color("LawnGreen") translate([SideTopStart + (SideTopHeight/2.0),SideTopWidth/2.0,OutsideBaseWidth/2.0]) rotate([90,90,90])
		 RoundTopBox( 0.1, OutsideBaseWidth, SideTopHeight, SideTopWidth,  1.5, 20);

//-- Upper Top Guide.

  color("LimeGreen") translate([SideTopStart+ (SideTopHeight/2.0),UpperTopStart + SideTopWidth/2.0,OutsideBaseWidth/2.0])
		 rotate([90,90,90])
		 RoundTopBox( 0.1, OutsideBaseWidth, SideTopHeight, SideTopWidth,  1.5, 20.0);

}

module BasePlate() {

	color("red") translate([SpoolPrintOffset, SideTrackWidth, 0])
	cube([SpoolBaseplateXorY,SpoolBaseplateXorY,SpoolBaseplateDepth]);
  
}

module MainTube() {
	
 	difference(){ 
	
    	color("Yellow") 
		translate([SpoolPrintOffset + (SpoolBaseplateXorY /2.0),SideTrackWidth + (SpoolBaseplateXorY / 2.0),SpoolBaseplateDepth-0.01])
		tube(SpoolDepth + SideTopHeight + 1.0,SpoolHoleDiameter/2.0,TubeThickness);
		
		color("Orange") 
		//  Leave 15mm lower collar to strengthen printing.
    	translate([SpoolPrintOffset,0,15])
		cube([SpoolBaseplateXorY,(SpoolBaseplateXorY  + TubeBaseClearance)/2,SpoolDepth  + SideTopHeight + 1.0 + TubeCollarWidth ]);
  }
}

module UpperCollar() {

	difference(){ 
    	color("SkyBlue")
 		translate([SpoolPrintOffset + (SpoolBaseplateXorY /2.0),SideTrackWidth + (SpoolBaseplateXorY / 2.0),SpoolDepth  + SideTopHeight + 1.0])
		tube(TubeCollarWidth,(SpoolHoleDiameter + TubeCollarHeight)/2.0,TubeCollarHeight);
		
    	translate([SpoolPrintOffset,0,0])
		cube([SpoolBaseplateXorY,(SpoolBaseplateXorY  + TubeBaseClearance)/2,SpoolDepth + SideTopHeight + 1.0 +TubeCollarWidth]);
  }
}

module SupportTriangle() {

	color("pink")
	translate([SpoolPrintOffset + (SpoolHoleDiameter /2.0)
			+ TubeBaseClearance,SpoolBaseplateXorY - TubeBaseClearance,SpoolBaseplateDepth-0.01]) rotate ([0,90,180])
	rightTriangle(SpoolDepth,SpoolHoleDiameter - TubeBaseClearance,TubeThickness);

}

//--	Spool Tube and support base.

module SpoolSupport() {

	BasePlate();
	MainTube();
	UpperCollar();
	SupportTriangle();
}