// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_Chewie, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable Chewie

// Parametric shirt clip 'chewie'
// (c) Laird Popkin, 2013

// Chewie or Clip? Print a Chewie in soft plastic (Nylon) and a set of clips in hard plastic (PLA)
print = 1; // [1:Chewie, 2:Clips]
// size of square chewie
width = 40;
// thickness of clip
bar = 4;
// height of chewie
height=8;
// thickness of fold area
thin = 1;
// length of fold area
gap=10;
// Thickness of wall at end of clip 'hole'
wall=1;
// Spacing of texture
step=5;
// Shape of texture 1
shape = 2; //[1:Flat, 2:Balls, 3:Cubes, 4:hlines, 5:vlines]
// Shape of texture 2
shape2 = 5; //[1:Flat, 2:Balls, 3:Cubes, 4:hlines, 5:vlines]
// Number of clips
numClips = 4;
// Angle clips in by this many degrees
clipAngle = 1;
// How much space around clips. This doesn't need to be particularly tight. 
loose = 0.5;
clipSize = bar-loose;

clipStep = width/(numClips+1);

//imageFile="minecraft_pickaxe/mine_pick.stl";
//imageScale=0.4*1;

foldGap = gap/2;
clipGap = foldGap+2*bar+2;

module clips() {
	for (y = [0:clipGap:clipGap*(numClips-1)]) {
		translate([0,y,0]) clip();
		}
	}

module clip() {
	rotate([0,0,clipAngle]) cube([width,clipSize,clipSize]);
	translate([0,foldGap+bar,0]) rotate([0,0,-clipAngle]) cube([width,clipSize,clipSize]);
	#translate([0,1,0]) cube([clipSize,foldGap+2*bar-2,clipSize]);
	}

module chewie() {
	difference() {
		union() {
			texture();
			//translate([width/2,width/2,height-0.5]) scale([imageScale,imageScale,imageScale]) import(imageFile);
			translate([width+gap,0,0]) texture2();
			cube([2*width+gap,width,height]);	// base shape
			}
	
		for (y = [clipStep-bar/2:clipStep:width-clipStep])
			translate([wall,y,thin]) cube([2*width+gap-2*wall,bar,bar]);	// clips
	
		translate([width,-1,thin]) cube([gap,width+2,height]); // gap where it folds
		}
	}

module texture() {
	echo(str("Shape is ",shape));

	if (shape == 2) balls();
	if (shape == 3) cubes();
	if (shape == 4) hlines();
	if (shape == 5) vlines();
	if (shape2 == 6) cylinders();
	}

module texture2() {
	echo(str("Shape2 is ",shape));

	if (shape2 == 2) balls();
	if (shape2 == 3) cubes();
	if (shape2 == 4) hlines();
	if (shape2 == 5) vlines();
	if (shape2 == 6) cylinders();
	}

module balls () {
	for (x = [step/2:step:width-step/2]) {
		for (y = [step/2:step:width-step/2]) {
			translate([x,y,height]) sphere(step/2,$fn=16);
			}
		}
	}

module cubes () {
	for (x = [step/2:step:width-step/2]) {
		for (y = [step/2:step:width-step/2]) {
			translate([x,y,height]) cube(step/2,center=true);
			}
		}
	}

module hlines() {
	for (x = [step/2:step:width-step/2]) {
		translate([x,0,height]) cube([1,width,1]);
		}
	}

module vlines() {
	for (y = [step/2:step:width-step/2]) {
		translate([0,y,height]) cube([width,1,1]);
		}
	}

module cylinders() {
	for (x = [step/2:step:width-step/2]) {
		for (y = [step/2:step:width-step/2]) {
			translate([x,y,height]) cyninder(r=step/2,h=1,$fn=16);
			}
		}
	}

if (print == 1) chewie();
if (print == 2) clips();