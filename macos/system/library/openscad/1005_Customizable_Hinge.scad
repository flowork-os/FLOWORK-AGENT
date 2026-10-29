// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_Hinge, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable Hinge

//Anthony Weber - agweber
//agweber@indiana.edu
// April 14, 2013

//Build Plate Library from MakerBot
//http://www.thingiverse.com/thing:44094
use <utils/build_plate.scad>;

//preview[view:east,tilt:top]

//for display only, doesn't contribute to final object
build_plate_selector = 1; //[0:Replicator 2,1: Replicator,2:Thingomatic]

//How many different hinge parts are there?
hingePieces = 4; //[2:24]

//Overall height (turns into this - tolerance!)
hingeHeight = 42;//[12:240]

//How wide is each side?
wingWidth = 18; //[18:120]

//How thick is each side?
wingThickness = 2; //[2:25]

//tolerance between the hinge cylinders, as well as other bits
tolerance = 0.3; 

//Diameter of the inner shaft
insideDiameter = 3; 

//Diameter of the outside hinge cylinder
outsideDiameter = 6;

//Screw holes? Needs more work!
numHoles = 2;

//How big are the holes?
holeDiameter = 8; 

//Print support for vertical print?
vertSupport = 1; //[0=No,1=Yes]

//Number of support points. Larger hinges will need more, smaller less.
numberOfSupports = 7;

//Support Thickness 
supportThickness = 0.4;

//Cylinder roundness. Higher is rounder, but takes more computation
cl = 42;

/*[Hidden]*/
//Above comment tells the customizer to stop looking for parameters

//Print only half TODO
printHalf = 0; //[0=No,1=Yes]

//Display Build Plate
build_plate(build_plate_selector);


//draw out the hinge!
//translate([0,-hingeHeight/2,wingThickness*2]) rotate([-90,0,0])
	hinge(hingeHeight, wingWidth, wingThickness, tolerance, insideDiameter,
			outsideDiameter, hingePieces);


	//todo:
	//-----add in a tolerance thick cube on the green wing

module hinge(l=50, w=10, th=5, t=1, id=5, od=10, i=5) { //length, width, thickness, tolerance
	//let's generate some variables!
	interval = l/i;
	numHingeA = round(i/2); //number of hinge parts on the first
	numHingeB = i-numHingeA; //number of hinge parts on a banana
	difference() {
		union() {
			cylinder(r=id/2,h=l,$fn=cl); 
			for (j = [0:numHingeA-1]) {
				union() {
					translate([0,0,interval*j*2]) cylinder(r=od/2, h=interval-t,$fn=cl);
					translate([0,od/2-th,interval*j*2]) cube([w,th,interval-t]);
					if (j < numHingeB) {
						translate([od/2+t,od/2-th,interval*j*2+interval-t])
							cube([w-od/2-t,th,interval+t]);
					}
				}
			}
			for (j = [0:numHingeB-1]) {
				difference() { //difference subtracts the center axle
					union() { //combines the cyl and side pieces
						translate([0,0,interval*j*2+interval]) color("green") cylinder(r=od/2, h=interval-t,$fn=cl);
//						translate([-w,od/2-th+t,interval*j*2-t])
//							color("green") cube([w-od/2-t,th-t,interval+t]);
						translate([-od/2-t-0.05,od/2-th+t,interval*j*2+interval])
							color("green") cube([od/2+t+0.1,th-t,interval-t]);
					}
					translate([0,0,interval*j*2+interval]) cylinder(r=(id+t)/2, h=interval-t,$fn=cl);
				}
			}
			//thicken the green side so its the same
			translate([-w,od/2-th,0]) color("orange")
				cube([w-od/2-t,th,l]);
			if (i%2 == 1) {
				translate([-w,od/2-th+t,interval*(i-1)-t])
					color("green") cube([w-od/2-t,th-t,interval+t]);
			}
		}
		//Now chop off any excess
		translate([-w,-w,-t*3]) cube([w*2.5,w*2.5,t*3]);
		translate([-w,-w,l-t]) cube([w*2.5,w*2.5,t*3]);
		//Holes? Sure!
		for (j = [0:numHoles-1]) {
			translate([wingWidth/3*2,wingThickness*3,(j+1)*hingeHeight/(numHoles+1)]) rotate([90,0,0])
				cylinder(r=holeDiameter/2, h=4*wingThickness,$fn=cl);
			translate([-wingWidth/3*2,wingThickness*3,(j+1)*hingeHeight/(numHoles+1)]) rotate([90,0,0])
				cylinder(r=holeDiameter/2, h=6*wingThickness,$fn=cl);
		}
	} //end difference
	//Vertical print support
	if (vertSupport != 0) {
		for (i=[1:i-1]) { //number of needed support spots
			for (j=[0:numberOfSupports]) {
				rotate([0,0,j*360/numberOfSupports])
				translate([insideDiameter/2+t,0,i*interval-t])
					color("red")
					cube([outsideDiameter/2-insideDiameter/2-t,supportThickness,t]);
			}
		}
	}
}