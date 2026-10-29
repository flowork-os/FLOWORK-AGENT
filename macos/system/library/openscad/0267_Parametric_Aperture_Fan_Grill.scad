// [FL_INDEX: keywords="openscad, 3d_parametric, Parametric_Aperture_Fan_Grill, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Parametric Aperture Fan Grill

/* [Body Parameters] */
// Fan Size
size=80;
// Border Width
borderthickness=5;
// Corner Radius 
cornerradius=4;
// Sheet Thickness 
thickness=2;

/* [Screw Hole Parameters] */
// Screw Radius 
screwradius=2.3;
// Screw Inset From Corder
screwinset=4;

/* [Spine Parameters] */
// Number of Spines
spines=10;
// Spine Thickness
spinesize=2;
// Spine Offset from center
spineoffset=10;
// Spine Extra Rotation
spinerotation=0;

/* [Hidden] */
dxf=false;
// Below are not parameters //

// Calculate helper variables
holeradius=size/2-borderthickness;

// Create the grill
if (dxf)
	projection(cut=false) fan_grill();
else
	fan_grill();

module fan_grill()
{
	union()
	{
		difference()
		{
			body();

			// hole
			translate([size/2,size/2,-thickness/4]) cylinder(r=holeradius,h=thickness*2);

			// screws
			translate([screwinset,screwinset,0]) cylinder(r=screwradius,h=thickness);
			translate([screwinset,size-screwinset,0]) cylinder(r=screwradius,h=thickness);
			translate([size-screwinset,screwinset,0]) cylinder(r=screwradius,h=thickness);
			translate([size-screwinset,size-screwinset,0]) cylinder(r=screwradius,h=thickness);
		}
		translate([size/2,size/2,0])
		interrior();
	}
}

module body()
{
	union()
	{
		translate([0,cornerradius,0]) cube(size=[size,size-(cornerradius*2),thickness]);
		translate([cornerradius,0,0]) cube(size=[size-(cornerradius*2),size,thickness]);
		translate([cornerradius,cornerradius,0]) cylinder(r=cornerradius,h=thickness);
		translate([cornerradius,size-cornerradius,0]) cylinder(r=cornerradius,h=thickness);
		translate([size-cornerradius,cornerradius,0]) cylinder(r=cornerradius,h=thickness);
		translate([size-cornerradius,size-cornerradius,0]) cylinder(r=cornerradius,h=thickness);
	}
}

module interrior()
{
	for(i=[0:spines-1])
	{
		  rotate(a=[0,0,i*(360.0/spines)+spinerotation]) 
		  translate([spineoffset,-spineoffset/3.141,0])
		  cube([spinesize,holeradius+(spineoffset/3.141),spinesize]);
	}
}