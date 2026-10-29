// [FL_INDEX: keywords="openscad, 3d_parametric, CoffeeCam__a_Shutter_for_Large_Format_Pinhole_Can_Cameras, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: CoffeeCam: a Shutter for Large Format Pinhole Can Cameras

// ===== file: TeaCam_tripod.scad =====
/* 		CoffeeCam Tripod mounts By schlem
		theschlem@gmail.com
	 	02/07/2014

A parametric assembly for mounting a 1/4-20
tripod nut on a cylindrical surface. Designed
to be expoxied in place holding a flanged nut
captive.
Also generates a version for mounting on flat 
surfaces.
The script is customizable for any can diameter.

*/

// ******** First Things ***********************  

$fn=120;

// ******** Parameters *************************  

// main parameters


can_d 		= 66.25;  		/* Diameter of coffee can, mm

							illy espresso can - 	91 mm
							Lavazza espresso can -	109 mm
							McCanns Irish Oats -	114 mm
							Quaker Oats -				128 mm
			
							*/

// misc parameters


mount_d 	= 35;			// diameter of mounting disk 

mount_t 	= 6;			// thickness of mounting disk

circ 		= 16;			// diam of circ hole

elev		= 3.75;			// height of circ hole 

nut 		= 11.35;		// nut size across flats, mm


// calculation to convert nut parameter
//  to a radius for a 6-sided "circle"
nut_diam 	= 2*(sqrt((nut*nut)/3));

echo ("nut size across points:", nut_diam, "mm");






// ******** Top Level code ********************* 

//translate([mount_d*0.66,0,mount_t/2]) 			// plated
//tmount(diam = mount_d, 
//		thick = mount_t, 
//		hole = circ, 
//		hole_h = elev,
//		hex = nut_diam);  


//translate([-mount_d*0.66,0,mount_t]) 			// plated
translate([0,0,mount_t]) 			// plated
tmount_curved(arc = can_d,
				diam = mount_d, 
				thick = mount_t*2, 
				hole = circ, 
				hole_h = elev,
				hex = nut_diam);  






// ******** Modules **************************** 

// ============ tmount =============

module tmount(diam = 25, 
				thick = 8, 
				hole = 15, 
				hole_h = 4,
				hex = 10,)	
{ 
	difference()
	{
		
		cylinder(h = thick, r=diam/2, $fs=4, center=true);

		hexagon(hgt=mount_t, w=hex);

		translate([0,0,hole_h])
		cylinder(h = thick, r=hole/2, $fs=4, center=true);
		
	}
}


// ============ tmount_curved =============

module tmount_curved(arc = 50,
						diam = 25, 
						thick = 8, 
						hole = 15,
						hole_h = 4,
						hex = 10,)	
{ 
		difference()
	{
		scale([1.5,1,1])
		cylinder(h = thick, r=diam/2, $fs=4, center=true);

		hexagon(hgt=mount_t*2, w=hex);

		translate([0,0,hole_h])
		cylinder(h = thick, r=hole/2, $fs=4, center=true);

		translate([0,0,(arc/2)])
		rotate([90,0,90])
		cylinder(h = diam*3, r=arc/2, $fs=4, center=true);
		
	}
}


// ============ hexagon =============

module hexagon(hgt=10, w=8)
{ 
		cylinder(h = hgt*2, r=w/2, $fn=6, center=true);
}



// ============ end =============/*



// ===== file: coffeecam.scad =====
/* 		CoffeeCam By schlem
		theschlem@gmail.com
	 	02/07/2014

A parametric pinhole and shutter assembly to turn
any can or cylinder into a large format pinhole
camera. Traditionally, a beginner's project in 
photography, using an oatmeal box, these parts
are customizable to any can diameter.

*/

// ******** First Things ***********************  

$fn=120;

// ******** Parameters *************************  

// main parameters

curved = true;			// if true, fits curved cylinder
							// of diameter can_d; if false,
							// makes a flat mount

can_d 		= 91;  		/* Diameter of coffee can, mm

							illy espresso can - 	91 mm
							Lavazza espresso can -	109 mm
							McCanns Irish Oats -	114 mm
							Quaker Oats -				128 mm
			
							*/

// misc parameters


ring_d 	= 52;			// Diameter of shutter ring 

blade 		=2; 			// thickness of shutter blade, mm

ring_t 	= 4;			// Thickness of ring
sp_t 		= blade+1;	// Thickness of shutter_plate
saddle_t	= 1.5;			// Thickness of saddle at thinest point 

hole 		= 12;			// Average H&W of square tapered hole

count 		= 45;  		// number of indents in ring
bolt 		= 3;			// bolt diameter, mm
offset		= 19;			// offset for bolt holes




// some simple trig is necessitated, since a four-sided 
// cylinder is measured diagonally, across the apices
adj_hole = sqrt(pow(hole,2)*2);

fudge = 1.03; 	// tolerance variable for shutter fit




// ******** Top Level code ********************* 

plated();
//assembled();


// ******** Modules **************************** 

// ============ plated =============

module plated()
{
	translate([50,30,0]) 			// plated
	ring(diam = ring_d, thick = ring_t, whole = adj_hole);  
		// diameter, thickness, nominal size of hole 
	
	
	translate([-45,17,0]) 			// plated
	shutter(ring_d, blade, adj_hole);
		// ring diameter, blade thickness, nominal size of hole
	
	
	translate([50,-30,0]) 			
	shutter_plate(dmtr = ring_d, thique = sp_t, hool = adj_hole);
		// ring diameter, shutter_plate thickness, nominal size of hole
	
	
	translate([0,0,0]) 		
	saddle(dm=ring_d, t=saddle_t, can=can_d/2);
		// ring diameter, saddle thickness, can diameter
}


// ============ assembled =============

module assembled()
{
	translate([0,0,sp_t])			
	ring(diam = ring_d, thick = ring_t, whole = adj_hole);  
		// diameter, thickness, nominal size of hole 
	
	
	translate([0,0,1])			
	shutter(ring_d, blade, adj_hole);
		// ring diameter, blade thickness, nominal size of hole
	
	
	translate([0,0,0])			
	shutter_plate(dmtr = ring_d, thique = sp_t, hool = adj_hole);
		// ring diameter, shutter_plate thickness, nominal size of hole
	
	

	mirror([0,0,1])			
	saddle(dm=ring_d, t=saddle_t, can=can_d/2);
		// ring diameter, saddle thickness, can diameter
}


// ============ ring =============

module ring(diam=30, thick=3, whole=20)	
{ 
	difference()
	{
		translate([0,0,thick/2])
		cylinder(h = thick, r=diam/2, $fs=4, center=true);

		translate([0,0,-saddle_t - sp_t-1])
		cone();

		// a=hole size, b=offset from center, c=height
		perf(bolt, offset, ring_t);

		translate([0,0,thick/2])
		henge(x=2, y=2, z=thick*1.1, offset=diam/2);

		translate([0,0,(thick/2)+3])
		cylinder(h = thick, r=diam*.9/2, $fs=4, center=true);
	}
}

// ============ shutter_plate =============

module shutter_plate(dmtr=30, thique=3, hool=20)
{ 
		difference()
		{	
			translate([0,0,thique/2])
			cylinder(h = thique, r=dmtr/2, $fs=4, center=true);
			
			union()
			{
				translate([0,0,blade/2+1])
				scale([fudge,fudge,1.05])
				cube(size = [hool*1.4,dmtr,blade], center = true);
				translate([0,dmtr/2,blade/2+1])
				scale([fudge,fudge,1.05])
				cylinder(h = blade, r = hool*0.9, center = true);
			}

			// a=hole size, b=offset from center, c=height
			perf(bolt, offset, sp_t);
	

			translate([0,0,-saddle_t-1])
			cone();
		}
}

// ============ shutter =============

module shutter(rd = 30, zed = 2, hd = 10)
{ 	
	difference()
	{	
		union()
		{
			translate([0,0,zed/2])
			cube(size = [hd*1.4,rd,zed], center = true);
			translate([0,rd/2,0])
			cylinder(h = zed, r = hd*0.9);
		
			translate([0,-2*hd,zed/2])
			cube(size = [hd*1.4,rd,zed], center = true);
			translate([0,-rd/2-2*hd,0])
			cylinder(h = zed, r = hd*0.89);
		}
		translate([0,0,-sp_t-.5])
		cone();
	}
}

// ============ saddle =============

module saddle(dm=30, t=3, can=10)
{ 
	difference()
	{
		translate([0,0,ring_d/2])
		cylinder(h = ring_d, r=dm/2, $fs=4, center=true);

		translate([0,0,1])
		cube(5.5,center=true);

		// a=hole size, b=offset from center, c=height
		perf(bolt, offset, can*1.1);

		translate([0,0,can/2])
		henge(x=2, y=2, z=can*1.1, offset=dm/2);

		
		if (curved)

		{
    		translate([0,0,(can)+t])
			rotate([90,0,90])
			cylinder(h = dm*1.2, r=can, $fs=4, center=true);
		} 
		else 
		{
		   translate([0,0,ring_d/2+2])
			cube(size = ring_d+2, center = true);
		}
	}
}



// ============ cone =============

module cone(min_d=0, max_d=hole*2.5, hite = (ring_t + sp_t + saddle_t) *1.3)
{ 

	rotate([0,0,45])
	translate([0,0,hite/2+1])
	cylinder
		(h = hite, r1 = min_d, r2 = max_d, $fn=4, center = true);
}



// ============ perf =============

module perf(a=4, b=20, c=10)
// a=hole size, b=offset from center, c=height
{
	translate([b,0,c/2])
	cylinder(h = c*1.1, r = a/2, center = true);
	
	mirror ([1,0,0])
	translate([b,0,c/2])
	cylinder(h = c*1.1, r = a/2, center = true);
}



// ============ henge =============

module henge(x=20, y=20, z=8, offset=20)

// I'm sure there is a better name for a concentric ring
// of columns, but I don't know what it is...
{
	for ( i = [0 : count-1] )
	{	 
		rotate([0,0,(360/count)*i])
		translate([offset,0,0])
			cylinder(h=z, r=x/2, center=true);
			//cube(size = [x,y,z], center = true);
	}
}

// ============ end =============/*



// ===== file: coffeecam_tripod.scad =====
/* 		CoffeeCam Tripod mounts By schlem
		theschlem@gmail.com
	 	02/07/2014

A parametric assembly for mounting a 1/4-20
tripod nut on a cylindrical surface. Designed
to be expoxied in place holding a flanged nut
captive.
Also generates a version for mounting on flat 
surfaces.
The script is customizable for any can diameter.

*/

// ******** First Things ***********************  

$fn=120;

// ******** Parameters *************************  

// main parameters


can_d 		= 91;  		/* Diameter of coffee can, mm

							illy espresso can - 	91 mm
							Lavazza espresso can -	109 mm
							McCanns Irish Oats -	114 mm
							Quaker Oats -				128 mm
			
							*/

// misc parameters


mount_d 	= 30;			// diameter of mounting disk 

mount_t 	= 6;			// thickness of mounting disk

circ 		= 16;			// diam of circ hole

elev		= 3;			// height of circ hole 

nut 		= 11.35;		// nut size across flats, mm


// calculation to convert nut parameter
//  to a radius for a 6-sided "circle"
nut_diam 	= 2*(sqrt((nut*nut)/3));

echo ("nut size across points:", nut_diam, "mm");






// ******** Top Level code ********************* 

translate([mount_d*0.66,0,mount_t/2]) 			// plated
tmount(diam = mount_d, 
		thick = mount_t, 
		hole = circ, 
		hole_h = elev,
		hex = nut_diam);  


translate([-mount_d*0.66,0,mount_t]) 			// plated
tmount_curved(arc = can_d,
				diam = mount_d, 
				thick = mount_t*2, 
				hole = circ, 
				hole_h = elev,
				hex = nut_diam);  






// ******** Modules **************************** 

// ============ tmount =============

module tmount(diam = 25, 
				thick = 8, 
				hole = 15, 
				hole_h = 4,
				hex = 10,)	
{ 
	difference()
	{
		cylinder(h = thick, r=diam/2, $fs=4, center=true);

		hexagon(hgt=mount_t, w=hex);

		translate([0,0,hole_h])
		cylinder(h = thick, r=hole/2, $fs=4, center=true);
		
	}
}


// ============ tmount_curved =============

module tmount_curved(arc = 50,
						diam = 25, 
						thick = 8, 
						hole = 15,
						hole_h = 4,
						hex = 10,)	
{ 
		difference()
	{
		cylinder(h = thick, r=diam/2, $fs=4, center=true);

		hexagon(hgt=mount_t*2, w=hex);

		translate([0,0,hole_h])
		cylinder(h = thick, r=hole/2, $fs=4, center=true);

		translate([0,0,(arc/2)])
		rotate([90,0,90])
		cylinder(h = diam*1.2, r=arc/2, $fs=4, center=true);
		
	}
}


// ============ hexagon =============

module hexagon(hgt=10, w=8)
{ 
		cylinder(h = hgt*2, r=w/2, $fn=6, center=true);
}



// ============ end =============/*

