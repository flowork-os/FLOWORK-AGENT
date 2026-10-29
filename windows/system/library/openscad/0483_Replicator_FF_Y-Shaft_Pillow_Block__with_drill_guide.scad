// [FL_INDEX: keywords="openscad, 3d_parametric, Replicator_FF_Y-Shaft_Pillow_Block__with_drill_guide, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Replicator/FF Y-Shaft Pillow Block, with drill guide

// ===== file: pillow.scad =====
// Y-AXIS SHAFT BEARING PILLOW BLOCK FOR REPLICATOR AND FLASHFORGE CREATOR
// Gary A. Crowell Sr.,  1/23/14


// temp bring in existing block to match sizes
//translate ([-5.5 -7 -10, -2, 0]) import_stl (file = "rep_bracket2B-V1.stl");


// Enter the distance from the inside of the panel to the opposite side of the 
// shaft - this distance includes the space from the panel to the shaft plus the 
// diameter of the shaft.  It's done this way because it's really easy to 
// measure this with the depth guage feature of a caliper.  I suggest you 
// measure each of the four pillow block locations - they may not be the same.

ShaftDist = 15.5;  // 15.5mm is the distance of the original block, 13mm + 2.5mm radius of shaft


CenterDist = ShaftDist - 2.5;
BearingOD = 11.35; // adjust for a friction fit of the bearing

echo ();
echo ("Measured Rod Distance - measured from");
echo ("inside wall to exterior of shaft away from wall");
echo ("...that is, the distance from wall to shaft,");
echo ("plus the shaft diameter, 5mm = ", ShaftDist);
echo ("Resulting distance, wall to shaft center = ", CenterDist);
echo ();

NutDia = 6.55;
NutHeight = 2.6;


difference() { 
 
	hull () { 
		translate ([-17, -CenterDist+13, 0]) cube (size = [34, 10+CenterDist-13, 8]); // main horizontal block
		translate ([0, 13, 0]) cylinder (h = 8, r = 9.0, $fn = 60); // circular bearing section
	} // hull

	// bolt holes - note: bolt holes must be large enough for a slip fit of the bolt - no threading
	translate ([14, 16, 4]) rotate (a = [90, 0, 0]) cylinder (h = 25, r = 3.5/2, $fn = 60);
	translate ([-14, 16, 4]) rotate (a = [90, 0, 0]) cylinder (h = 25, r = 3.5/2, $fn = 60);
	translate ([0, 13, 5]) rotate (a = [90, 0, 220]) cylinder (h = 20, r = 3.0/2, $fn = 60); // bearing setscrew
	
	translate ([0, 13, -1]) cylinder (h = 10, r = 3.5, $fn = 60); // central thru hole
	translate ([0, 13, 2]) cylinder (h = 8, r = BearingOD/2, $fn = 60); // bearing hole
	
	// nut voids, open to end surface
	hull () { 
		translate ([-14, 8, 4]) rotate (a = [90, 0, 0]) cylinder (h = NutHeight, r = NutDia/2, $fn = 6);
		translate ([-18, 8, 4]) rotate (a = [90, 0, 0]) cylinder (h = NutHeight, r = NutDia/2, $fn = 6);
	} // hull
	hull () { 
		translate ([14, 8, 4]) rotate (a = [90, 0, 0]) cylinder (h = NutHeight, r = NutDia/2, $fn = 6);
		translate ([18, 8, 4]) rotate (a = [90, 0, 0]) cylinder (h = NutHeight, r = NutDia/2, $fn = 6);
	} // hull
	
} // difference


// exterior plate
difference() { 
	hull () { 
		translate ([14.5, -10, 0]) rotate (a = [0, 0, 0]) cylinder (h = 1.2, r = 4, $fn = 30);
		translate ([-14.5, -10, 0]) rotate (a = [0, 0, 0]) cylinder (h = 1.2, r = 4, $fn = 30);	
	} // hull
	translate ([14, -10, -1]) cylinder (h = 5, r = 3.4/2, $fn = 60);
	translate ([-14, -10, -1]) cylinder (h = 5, r = 3.4/2, $fn = 60);
} // difference

// ===== file: pillow_drill.scad =====
// Replicator Pillow Block Drill Guide
// Gary A. Crowell Sr.,  1/14/15


//This thing is a drill guide for mounting the y-axis shaft pillow blocks, 
//http://www.thingiverse.com/thing:232678


/*
// display the upper corner of the Replicator

difference() { 
	hull () { // side
		translate ([0, -5.4+35, -50]) cube (size = [5.6, 50, 50]);
		translate ([0, -5.4, -50-35]) cube (size = [5.6, 50, 50]);
	}
	translate ([-10, 13+5.6, -17-5.4-3.6]) rotate (a = [0, 90, 0]) cylinder (h = 20, d = 11, $fn = 30);
}

hull () { // back
	translate ([5.6+32, 0, -50]) cube (size = [50, 5.6, 50]);
	translate ([5.6, 0, -50-32]) cube (size = [50, 5.6, 50]);
}
hull () { // top
	translate ([5.6+28, 5.6, -5.6-3.6]) cube (size = [50, 50, 5.6]);
	translate ([5.6, 5.6+28, -5.6-3.6]) cube (size = [50, 50, 5.6]);
}
*/
//shaft
//translate ([0, 13+5.6, -18-5.4-3.6]) rotate (a = [0, 90, 0]) cylinder (h = 100, d = 5, $fn = 30);
	
	
		

//shaft center from top edge of side panels
shaftcenter = 27;
	
translate ([0, -26.5, 0]) {		
// measure the distance from the top edge to the center of the y-shaft
difference() { 
	translate ([-2, 0, -45]) cube (size = [2, 90, 45]); 
	translate ([-10, 45, -shaftcenter]) rotate (a = [0, 90, 0]) cylinder (h = 100, d = 7, $fn = 30);
	translate ([-10, 45, -shaftcenter+14]) rotate (a = [0, 90, 0]) cylinder (h = 100, d = 3.5, $fn = 30);	
	translate ([-10, 45, -shaftcenter-14]) rotate (a = [0, 90, 0]) cylinder (h = 100, d = 3.5, $fn = 30);	
	translate ([-10, 33, -43]) rotate (a = [0, 90, 0]) cylinder (h = 100, d = 8, $fn = 30);	
	translate ([-10, 90-33, -43]) rotate (a = [0, 90, 0]) cylinder (h = 100, d = 8, $fn = 30);

}
// upper lip that sits on top of back or front panels
translate ([-2, 0, 0]) cube (size = [9, 90, 2]); 

}

translate ([6, 5.5, -3.75]) #cube (size = [40, 6, 6]); 

difference() { 
translate ([-2, 5.6, 2]) cube (size = [15, 6, 4]); 
translate ([0, 4.6, 7]) rotate (a = [0, 15, 0]) cube (size = [15, 8, 4]); 
}

hull () { 
translate ([25, 5.6, 0]) cube (size = [2, 6, 2]); 
translate ([-2, -5, 0]) cube (size = [9, 30, 2]); 
}










