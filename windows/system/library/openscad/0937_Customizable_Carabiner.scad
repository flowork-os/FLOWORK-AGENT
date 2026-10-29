// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_Carabiner, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable Carabiner

// Title: Key Carabiner
// Author: http://www.thingiverse.com/Jinja
// Date: 17/12/2012

/////////// START OF PARAMETERS /////////////////

// the first smaller radius
radius1 = 6;    

// the second larger radius
radius2 = 11;   

// the distance between the centers of the radii
length = 36;    

// the thickness of the body
width = 6; 

// the height of the body
height = 6;     

// the width of the gap that cuts the body
gap = 0.39;     

// the angle of overhang your printer can manage
overhang = 40;  //[35:45]

// the mm width of the bevelled edge
rounded = 1;    

/////////// END OF PARAMETERS /////////////////

$fs=0.3*1;
$fa=5*1; //smooth
//$fa=20*1; //rough


module loop( height, length, width, radius1, radius2 )
{
	minkowski()
	{
		translate([0,0,rounded])
		difference()
		{
			swept_cylinder( height-2*rounded, length, radius1+width-rounded, radius2+width-rounded );
			swept_cylinder( height-2*rounded, length, radius1+rounded, radius2+rounded );
		}
		diamond();
	}

}

thick = 1.2*1;


difference()
{
	difference()
	{
		loop( height, length, width, radius1, radius2 );
		difference()
		{
			translate([0,0,thick])
			loop( height-2*thick, length, width-2*thick, radius1+thick, radius2+thick );
			cube([3*radius1+width,3*radius1+width,3*radius1+width],true);

			translate([length-(thick/cos(60)),radius2-width,height*0.5])
			rotate([0,45,60])
			{
				cube([height*2, length, gap+2*thick]);
				cube([gap+2*thick, length, height*2]);
			}

		}
	}
	translate([length,radius2-width,height*0.5])
	rotate([0,45,60])
	{
		cube([height*2, length, gap]);
		cube([gap, length, height*2]);
	}
}


module swept_cylinder( height, length, radius1, radius2 )
{
	hull()
	{
		cylinder( height, radius1, radius1 );
		translate( [length,0,0] )
		cylinder( height, radius2, radius2 );
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

module diamond()
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

