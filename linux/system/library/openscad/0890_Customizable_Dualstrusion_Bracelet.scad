// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_Dualstrusion_Bracelet, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable Dualstrusion Bracelet

// Title: Bracelet
// Author: http://www.thingiverse.com/Jinja
// Date: 23/2/2013

/////////// START OF PARAMETERS /////////////////

// The thickness of the structure. mm =
link_diameter = 25; //[14:32]

// The diameter of the bracelet. mm = 
bracelet_diameter = 84; //[30:300]

// Choose which colour to output for dual extruders
extruder_colour = "BothColours"; // [Colour1,Colour2,BothColours]

/////////// END OF PARAMETERS /////////////////
overhang=40*1;
thick=link_diameter/7;
rad = bracelet_diameter/2;
oangle = 45*1;
rings = 4 * floor(((rad*2*3.14159)/(sin(45)*thick*7))/2);
angle = 360/rings;
corner=0.9*1;

if(( extruder_colour == "BothColours" ) || ( extruder_colour == "Colour1" ))
{
for(i=[0:angle*4:359])
{
	rotate([0,0,i])
	translate([0,rad,0])
	rotate([0,0,oangle])
	rotate([0,90,0])
	{
		minkowski()
		{
			oct_tube( thick*5+(2*corner), thick-(2*corner), thick-(2*corner) );
			diamond(corner);
		}
	}

	rotate([0,0,i+angle*3])
	translate([0,rad,0])
	rotate([0,0,oangle])
	rotate([0,90,0])
	{
		minkowski()
		{
			oct_tube( thick*5+(2*corner), thick-(2*corner), thick-(2*corner) );
			diamond(corner);
		}
	}
}
}

if(( extruder_colour == "BothColours" ) || ( extruder_colour == "Colour2" ))
{
for(i=[0:angle*4:359])
{
	rotate([0,0,i+(2*angle)])
	translate([0,rad,0])
	rotate([0,0,oangle])
	rotate([0,90,0])
	{
		minkowski()
		{
			oct_tube( thick*5+(2*corner), thick-(2*corner), thick-(2*corner) );
			diamond(corner);
		}
	}

	rotate([0,0,i+angle*3+(2*angle)])
	translate([0,rad,0])
	rotate([0,0,oangle])
	rotate([0,90,0])
	{
		minkowski()
		{
			oct_tube( thick*5+(2*corner), thick-(2*corner), thick-(2*corner) );
			diamond(corner);
		}
	}
}
}

if(( extruder_colour == "BothColours" ) || ( extruder_colour == "Colour1" ))
{
	for(i=[0:angle*4:359])
	{
		hull()
		{
			rotate([0,0,i])
			translate([0,rad,0])
			rotate([0,0,oangle])
			rotate([0,90,0])
			{
				translate([0,thick*3,0])
				cube([thick,thick,thick*0.25],true);
			}
	
			rotate([0,0,i+(3*angle)])
			translate([0,rad,0])
			rotate([0,0,oangle])
			rotate([0,90,0])
			{
				translate([0,-thick*3,0])
				cube([thick,thick,thick*0.25],true);
			}
		}
	}
}

if(( extruder_colour == "BothColours" ) || ( extruder_colour == "Colour2" ))
{
	for(i=[0:angle*4:359])
	{
		hull()
		{
			rotate([0,0,i+(2*angle)])
			translate([0,rad,0])
			rotate([0,0,oangle])
			rotate([0,90,0])
			{
				translate([0,thick*3,0])
				cube([thick,thick,thick*0.25],true);
			}
	
			rotate([0,0,i+(3*angle)+(2*angle)])
			translate([0,rad,0])
			rotate([0,0,oangle])
			rotate([0,90,0])
			{
				translate([0,-thick*3,0])
				cube([thick,thick,thick*0.25],true);
			}
		}
	}
}


module cutter(dist, overhang)
{
	size = dist*2;

	translate([dist,-dist,-dist])
	cube([size,size,size]);

	translate([-dist-size,-dist,-dist])
	cube([size,size,size]);

	translate([dist,-dist,0])
	rotate([0,-overhang,0])
	cube([size,size,size]);

	translate([-dist,-dist,0])
	rotate([0,-90+overhang,0])
	cube([size,size,size]);

	translate([dist,-dist,0])
	rotate([0,90+overhang,0])
	cube([size,size,size]);

	translate([-dist,-dist,0])
	rotate([0,180-overhang,0])
	cube([size,size,size]);

}

module diamond( rounded )
{
	dist = rounded;
	difference()
	{
		cube([2*rounded,2*rounded,2*rounded], true);
		for(i=[0:45:179])
		{
			rotate([0,0,i])
			cutter(dist, overhang);
		}
	}
}



module oct_hole( diameter, length, thickness )
{
	oct_tube( 0, length, diameter*0.5 );
}

module oct_tube( diameter, length, thickness )
{
	radius = (diameter+thickness)*0.5;

	oct_side = diameter / (1+(2*sin(45)));
	oct_side2 = oct_side + thickness*tan(22.5)*2;

	union()
	{
		translate( [ radius, 0, 0] )
		cube( [thickness, oct_side2, length], true );
	
		rotate( [0,0,45] )
		translate( [ radius, 0, 0] )
		cube( [thickness, oct_side2, length], true );
	
		rotate( [0,0,90] )
		translate( [ radius, 0, 0] )
		cube( [thickness, oct_side2, length], true );
	
		rotate( [0,0,135] )
		translate( [ radius, 0, 0] )
		cube( [thickness, oct_side2, length], true );
	
		rotate( [0,0,180] )
		translate( [ radius, 0, 0] )
		cube( [thickness, oct_side2, length], true );
	
		rotate( [0,0,225] )
		translate( [ radius, 0, 0] )
		cube( [thickness, oct_side2, length], true );
	
		rotate( [0,0,270] )
		translate( [ radius, 0, 0] )
		cube( [thickness, oct_side2, length], true );
	
		rotate( [0,0,315] )
		translate( [ radius, 0, 0] )
		cube( [thickness, oct_side2, length], true );
	}
}
