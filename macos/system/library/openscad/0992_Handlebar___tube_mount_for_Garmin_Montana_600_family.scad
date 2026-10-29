// [FL_INDEX: keywords="openscad, 3d_parametric, Handlebar___tube_mount_for_Garmin_Montana_600_family, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Handlebar / tube mount for Garmin Montana 600 family 

// Set to "no" for printing:
print_it=0; // [1:yes,0:no]

// Print one "nut" and two "arm"s:
what="both"; // [both,nut,arm]

// Handlebar diameter:
handlebar_d=23.2;


//
// Handlebar support for Garmin Montana GPS - Rev 1.01
//
// CC-BY-NC 2013 by Jeremie.Francois@gmail.com / MoonCactus on thingiverse
// http://betterprinter.blogspot.com
//
// It slices neatly on an ultimaker with the following parameters
//
// 0.2 mm layers
// 1.8 mm walls (loops->infill->perimeters)
// 1.2mm bottom/top
// 30% fill
// 

// handlebar_d: [15:32]

// decathlon rockrider 500 = 23.2

tol=0+0.1;

// Main thickness
th= 0+4;
hnut_th= 0+5;

hook_x=0+19; // from center
hook_y=0+19-0.8; // 19mm from screen towards the back
hook_z=0+34 + 1.2; // from center// V1 was "1"

hook_szx= 0+8;
hook_szy= 0+2.8; // v1 was 2
hook_szz= 0+3;

arm_th= 0+6;

gps_szx= 0+145;
gps_szy= 0+37;
gps_szz= 0+75;

// How far is the handlebar (display only)
handle_y= 19+th + handlebar_d/2;


module body(w,h, margin)
{
	color([1,1,0])
	{
		scale([1,1.02,1])
		translate([-2,-2.1-0.6,-w/2]) linear_extrude(height=w) scale(0.192) import(file = "montana_large.dxf");

		rotate([0,90,0])
		translate([0.32,-0.45,-h/2])
		rotate([0,0,0.7]) linear_extrude(height=h) scale([0.08,0.082,0.08]) import(file = "montana_short.dxf");
	}
}

module ccyl(r,h, rot=[0,0,0])
{
	rotate(rot) translate([0,0,-h/2]) cylinder(r=r,h=h, $fs=0.5);
}



// hook
module hook()
{
	color([1,0.5,0.5])
		translate([0,-gps_szy/2, 0])
		{
			translate([hook_x,hook_y,hook_z])
			{
				hull()
				{
					ccyl(r=hook_szy/2, h=hook_szx, rot=[0,90,0]);
					translate([0,0,hook_szz]) ccyl(r=hook_szy/2, h=hook_szx, rot=[0,90,0]);
				}
			}
		}
}

module back_plate()
{
	hull()
	{
		translate([0,20,20]) rotate([0,90,0]) ccyl(r=2.4,h=arm_totszx,$fs=1);
		translate([0,20,0]) rotate([0,90,0]) ccyl(r=2.4,h=arm_totszx,$fs=1);
	}
}

arm_totszx= hook_x*2 + hook_szx;
module roundedarmtop()
{
	difference()
	{
		intersection()
		{
			union()
			{
				hull()
				{
//					translate([2,1,gps_szy- gps_szy/2-0.5]) rotate([0,90,0]) ccyl(r=gps_szy/2+th, h=arm_totszx);
				scale([1,1.2,1])
					translate([0,-2.5,gps_szy- gps_szy/2-0.5])
						rotate([0,90,0]) ccyl(r=gps_szy/2+th, h=arm_totszx);
					translate([0,-8,34- 15/2])
						rotate([0,90,0]) ccyl(r=15, h=arm_totszx);
				}
				back_plate();

				// protruding bit to open the arms
				hull()
				{
					translate([0,-13.5+2,gps_szz-37+8])
						rotate([0,90,0]) ccyl(r=2.4,h=arm_totszx,$fs=1);
					translate([0,-13.5+5,gps_szz-37+2])
						rotate([0,90,0]) ccyl(r=2.4,h=arm_totszx,$fs=1);
				}

			}
			union()
			{
				translate([0,-13.5,gps_szz-37]) rotate([0,90,0]) ccyl(r=2.4,h=100,$fs=1);
				translate([-50,-14,-tol]) cube([100,50,100]);
			}
		}
		body(1,gps_szx-80, 3); // remove on X axis
	}
}

// viewed from the back
module arm_half()
{
	difference()
	{
		roundedarmtop();
		// cut them in half
		cube([hook_x*2 - arm_th*2,gps_szy+th*4+tol,gps_szz+th*2+tol+20],center=true);
	}
}

module arms()
{
	for(mz=[-1:+1])
	{
		scale([1,1,mz])
		{
			arm_half();
			hook(); scale([-1,1,1]) hook();
		}
	}
}


module handlebar()
{
	translate([0,handle_y,0])
		rotate([0,90,0])
			ccyl(r=handlebar_d/2,h=100);
}

module back()
{
	// Back plate
	difference()
	{
		hull()
		{
			intersection()
			{
				union() { back_plate(); scale([1,1,-1]) back_plate(); }
				body(1,gps_szx-80, 3); // remove on X axis
			}
			translate([0,20+th,0]) cube([arm_totszx,th,41],center=true);
		}
	}
}

module fullgrip()
{
	difference()
	{
		union()
		{
			arms();
			back();
		}

		// screw holes
		screwset("onlyscrews");
		handlebar();
	}
}



module screw()
{
	cylinder(r=6/2+0.5, h=3, $fs=1); // screw head
	cylinder(r=3/2+0.2, h=30, $fs=1); // screw head
}

module screwset(what="onlyscrews")
{
	for(sz=[-1:2:1])
		for(sx=[-1:2:1])
			translate([11*sx,17,(handlebar_d/2+hnut_th/2)*sz])
				for(mz=[-1:1])
					scale([1,1,mz])
						rotate([-90,0,0])
		{
			screw();
			if(what!="onlyscrews")
				translate([0,0,handle_y-handlebar_d/2-10 + handlebar_d*0.4])
					cylinder(r1=6.01/2,r2=6.01/2+5,h=40,$fn=6);
		}
}


module handle_nut()
{
	difference()
	{
		hull()
		{
			translate([0,handle_y,0])
			{
				rotate([0,90,0])
					ccyl(r=handlebar_d/2+hnut_th, h=arm_totszx);

				translate([0,-handlebar_d/2,0])
					cube([arm_totszx,tol,handlebar_d+hnut_th*2],center=true);
			}
		}
		screwset("nuts");
		hull()
		{
			handlebar();
			translate([0,-20,0]) handlebar();
		}
		translate([0,handle_y-handlebar_d/2-10,0])
			cube([arm_totszx+tol,34,gps_szz],center=true);
		translate([0,handle_y+handlebar_d-hnut_th,0])
			sphere(r=handlebar_d/2);
	}
}


if(what=="nut" || what=="both")
{
	rotate([0,print_it?90:0,0]) // uncomment this to lay it flat for printing
		handle_nut();
}

if(what=="arm" || what=="both")
{
	rotate([0,print_it?90:0,0])
	intersection()
	{
		fullgrip();
		if(print_it)
			translate([0,-50,-50]) cube([100,100,100]); // only half of the stuff
	}
}
// %cube([gps_szx,gps_szy,gps_szz],center=true); // ghost of the device