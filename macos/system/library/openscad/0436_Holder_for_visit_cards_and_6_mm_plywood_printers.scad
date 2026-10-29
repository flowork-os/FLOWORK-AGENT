// [FL_INDEX: keywords="openscad, 3d_parametric, Holder_for_visit_cards_and_6_mm_plywood_printers, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Holder for visit cards and 6 mm plywood printers

tol=0.05;
th=1.2; // box wall thickness

ply_th= 6; // plywood thickness
hook_th= 3;
hook_sz= 4; // clamp height
hook_top_len= ply_th + hook_th;

vc_w= 55+1; // width of hole for vcard
vc_th_int= 10; // hole thickness (ie. how many card can be packed into the holder)
vc_th_ext= th + vc_th_int + th;

hook_width_ext=th+vc_w+th;
total_h= 30;

module ccube(size)
{
	translate([-size[0]/2, -size[1]/2, 0])
		cube(size);
}

difference()
{
translate([-hook_width_ext/2,0,0])
	union()
	{
		cube([hook_width_ext, vc_th_ext, total_h]);
		translate([0,vc_th_ext-tol,total_h-hook_th-tol])
		{
			cube([hook_width_ext, hook_top_len, hook_th]);
			translate([0,ply_th,-hook_sz])
				cube([hook_width_ext, hook_sz, hook_sz+hook_th]);
		}
	}

	// Main hole
	translate([-hook_width_ext/2,0,0])
		translate([th,th,th])
			cube([vc_w, vc_th_int, total_h]);
/*
	translate([-hook_width_ext/2+4,0,-10])
		translate([th,th,th])
			cube([vc_w-8, vc_th_int, total_h]);

	translate([0,0,total_h/2])
		carve_hole();
		
	for(dx=[-1,+1])
		for(dz=[-1,+1])
			translate([dx*subhole_dist, 0, dz*subhole_dist+total_h/2])
				scale([0.3,1,0.3])
					carve_hole();
*/
}
subhole_dist=18;

module carve_hole()
{
	translate([0,-1,0])
	{
		rotate([-90,0,0])
		{
			hull()
			{
				scale([1,0.6,1]) cylinder(r=16,h=vc_th_ext+2);
				scale([0.1,1,1]) cylinder(r=23,h=vc_th_ext+2);
			}
		}
	}
	
}