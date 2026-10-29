// [FL_INDEX: keywords="openscad, 3d_parametric, Parametric_Camera_Filter_Adapter, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Parametric Camera Filter Adapter

// ===== file: P66_filter_adapter.scad =====
/* Parametric Filter Holder

for the P6*6

3D Printed Pinhole Camera

http://www.thingiverse.com/thing:157844

By schlem

theschlem@gmail.com

01/29/2014



Designed for the Thingiverse Customizer

To allow for mounting any sized filter on the front

of the P6*6. For best results, the optional trim

ring should be mounted on the face of the "Shutter

Clamp" http://www.thingiverse.com/thing:219829



Using a Neutral Density filter can increase an

exposure duration to a usable speed in bright light.

Too much light means an impossible fast shutter speed

for a hand shuttered camera. Color filters can

compensate for, or create color shifts.

*/



// ******** First Things ***********************



$fn=120;



// ******** Parameters *************************

// All measurements in mm




filter_OD = 54.50; 	// OD of filter in threaded frame
							// sized for 52mm filters I bought
							// through Amazon.com

clip_OD = 50.92; 		// OD of "lens" cylinder
							// sized for P6*6, use 49.20 for Holga 120

ring = 3; 				// thickness of ring around larger diameter

filter_h = 6.5; 		// height of filter
lens_h = 3;				// height of "lens" cylinder 

height = 
	filter_h+lens_h;	// overall height

fudge = 0.80; 			// mm added to inside diameters for best fit

count= 45; 				//number of indentions in perimeter


// ******** Top Level code *********************

// Determine larger of the two diameters and construct adapter
// orients the larger diameter above the smaller for no overhang

if (filter_OD > clip_OD)
{
	translate([0,0,height/2])
	difference()
	{
		cylinder(h = height,r = ring + (filter_OD + fudge)/2, center = true);

		translate([0,0,-lens_h/3])
		cylinder(h = height*2, r = (clip_OD + fudge)/2, center = true);

		translate([0,0,lens_h])
		cylinder(h = height, r = (filter_OD + fudge)/2, center = true);

		henge(x=2, y=2, z=height*2, offset=ring + (filter_OD + fudge)/2);
	} 
	
} 
else  		// to be fixed
{
	translate([0,0,adapter_h/2])
	difference()
	{
		cylinder(h = height,r = ring + (clip_OD + fudge)/2, center = true);
	
		translate([0,0,-filter_h/3])
		cylinder(h = height*2 ,r = (filter_OD + fudge)/2, center = true);
	 
  		translate([0,0,filter_h])
		cylinder(h = height, r = (clip_OD + fudge)/2, center = true);

		henge(x=2, y=2, z=height*2, offset=ring + (clip_OD + fudge)/2);
	}
}


// ******** Modules ****************************


module henge(x=20, y=20, z=8, offset=20)
// I'm sure there is a better name for a concentric ring
// of columns, but I don't know what it is...
// But thanks to Eddie Izzard for this term!
// x and y control the dimensions of cube, if used
{
	echo (offset);
	for ( i = [0 : count-1] )
	{	 
		rotate([0,0,(360/count)*i])
		translate([offset,0,0])
			cylinder(h=z, r=x/2, center=true);
			//cube(size = [x,y,z], center = true);
	}
}
















// ============ name =============

// module module(P1=, P2=, P3=){ }


/* camera_trim By schlem
theschlem@gmail.com
01/02/14

This generates a radial pattern of negative spaces for
onamenting a trim ring designed to embelish the P6*6
3DPrinted Pinhole Camera -
http://www.thingiverse.com/thing:157844

All measurements in mm


// ******** First Things ***********************

$fn=120;

// ******** Parameters *************************

id=51; // diam of outside perimeter to be indented
inset=1.2;	 // depth of indent in perimeter
height=8;	 // height of neg space
width=1.50;	 // width of each indent
count=45;	 // number of indentions in perimeter

span=id/2;
block_x=2*inset;


// I'm sure there is a better name for a concentric ring
// of columns, but I don't know what it is...
henge();


// ******** Top Level code *********************

module henge(x=block_x, y=width, z=height, offset=span)
{
echo (offset);
for ( i = [0 : count-1] )
{	 rotate([0,0,(360/count)*i])
translate([offset,0,z/2])
// cylinder(h=z, r=block_x/2, center=true);
cube(size = [x,y,z], center = true);
}
}
*/


// ===== file: test_rings.scad =====
/* 		Calibration Rings By schlem
			theschlem@gmail.com
	 		02/02/14

Use these rings to measure reduction/increase of 
inside/ outside diameters and test infill per-
centages on YOUR printer



*/

// ******** First Things ***********************  

$fn=120;

// ******** Parameters ************************* 
// all units in mm
// creates two rings, 40mm outside diam / 36mm ID
//	and 20mm outside diam / 16mm ID
// Use the actual diamters to calculate the "fudge"
// variable in filter_holder.scad

 
OD1 = 40;	// big ring
ID1 = 36;

OD2 = 20; 	// little ring
ID2 = 16;

hgt = 3;		// height of rings




// ******** Top Level code ********************* 

ring(OD1,ID1,hgt);
ring(OD2,ID2,hgt);


// ******** Modules **************************** 

// ============ name =============

module ring(od=25, id=22.5, ht=6)
{ 
	difference()
	{
		translate([0,0,ht/2])
		cylinder(r=od/2,h=ht, center=true);
		#cylinder(r=id/2,h=ht*3, center=true);
	}


}



