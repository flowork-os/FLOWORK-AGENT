// [FL_INDEX: keywords="openscad, 3d_parametric, Magnetic_Mount_for_Jumper_Wire_Rack, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Magnetic Mount for Jumper Wire Rack

// This script creates a wire rack with a variable number of tines

$fn = 32;

// Tine dimensions
N = 8;			// Number of tines
tine_w = 10;
tine_h = 4;
tine_length = 30;
tine_pitch = 12;

// Base dimensions
base_h = 20;
base_w = base_h*2 + (N-1)*(tine_pitch) + tine_w;
base_t = 8;

// Endcap dimensions
cap_t = 12;

// Magnet inlay dimensions
M = 2;		// Number of magnetics
//mag_w = 4.2;
//mag_h = 10.2;
mag_t = 6;
mag_d = 12.6 + 0.2;
mag_offs = base_w/5;
mag_pitch = base_w*3/5;


echo("<b>Base width [mm]:", base_w);

// Mounting hole dimensions
countersink_d = 0;
screw_d = 2;

difference()
{
	// Baseplate
	union()
	{
		translate([base_h/2,0,0]) cube([base_w-base_h,base_h,base_t]);
		translate([base_h/2,base_h/2,base_t-cap_t]) cylinder(cap_t,base_h/2,base_h/2);
		translate([base_w-base_h/2,base_h/2,base_t-cap_t]) cylinder(cap_t,base_h/2,base_h/2);		
	}

	// Screw holes
	for (i = [0:1])
	{
		translate([base_h/2+(base_w-base_h)*i,base_h/2,base_t])
		{
			union()
			{
				// Countersink
				cylinder(base_t,countersink_d/2,countersink_d/2,true);

				// Screw hole
				cylinder(cap_t*3,screw_d/2,screw_d/2,true);
			}

		}
	}

	// Text
	/*translate([base_w/2-10.75*2.4,2,base_t-1])
		scale([12,12,2])
			import("WireRackText.stl");*/

	// Magnet inlays
	for (i = [0:(M-1)])
	{
		translate([mag_offs + mag_pitch*i, base_h/2, base_t-mag_t])
		{
			cylinder(mag_t+1, mag_d/2, mag_d/2);

			// Hole for magnet removal 
			cylinder(base_t*2, 3.5/2, 3.5/2, true);
		}
	}
}

// Tines
/*for (i = [0:(N-1)])
{
	// Tine
	translate([base_h + tine_pitch*i, base_h - tine_h, 0])
		cube([tine_w,tine_h,tine_length]);

	// Tine support
	translate([base_h + tine_pitch*i, base_h-tine_h, 0])
		rotate([45, 0, 0])
			cube([tine_w, tine_h, tine_h]);

	// Upturned tine end
	translate([base_h+tine_pitch*i,base_h-tine_h,tine_length])
		rotate([-30,0,0])
			cube([tine_w,tine_h,tine_h]);
}*/



