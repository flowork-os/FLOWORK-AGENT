// [FL_INDEX: keywords="openscad, 3d_parametric, PegStats, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: PegStats

// ===== file: Stats_Pegs.scad =====
use <write/Write.scad>;

//The target average of the set
ave=4.5;
//The target standard deviation of the set
std=1.5;
//Size of the matrix (columns and rows)
size=10;

/* [Hidden] */
$fn=100;

for (x = [0:size-1])
{
	for (y = [0:size-1])
	{
	difference ()
		{
			translate([x*15,y*15,0]) cylinder (r=6.8,h=10,center=true);
			translate([x*15,y*15,5])rotate([0,0,n*35]) write(str(round(std*sqrt(-2*ln(rands(0,1,1)[0]))*cos(360*rands(0,1,1)[0])+ave)),h=8,t=3, center=true);
			
		}
	}
}

// ===== file: Stats_holder.scad =====
use <write/Write.scad>;

//How many tubes?
tubes=8; // [1:30]
//Starting tube number?
numstart=1;
//Label the tubes with numbers?
numbers="Yes";  // [Yes,No]

/* [Hidden] */
$fn=100;

width=tubes*16; //increments of 16

difference()
	{
		cube ([width+1,115,13]);

	for (x=[0:width/16+1])
		{
		translate([x*16-7.5,5,8]) rotate([-90,0,0]) cylinder (r=7.1,h=120);
		translate([x*16-7.5,15,-1])cylinder (r=2.5,h=4);
		translate([x*16-7.5,65,-1])cylinder (r=2.5,h=4);
		translate([x*16-7.5,55,-1])cylinder (r=2.5,h=4);
		translate([x*16-7.5,105,-1])cylinder (r=2.5,h=4);
		translate([x*16-10,15,-1])cube([5,40,4]);
		translate([x*16-10,65,-1])cube([5,40,4]);
		}
	for (y=[0:9])
		{
		translate([-1,y*10+14,12]) cube([width+5,1,2]);
		}
	}
difference() {
	cube ([width+1,5,25]);
	if (numbers=="Yes")
		{
		for (c=[1:tubes])
			{
			translate([c*16-10,4,23]) rotate([90,180,180]) write(str(numstart+c-1),h=8, t=4);
			}
		}
	}