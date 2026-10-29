// [FL_INDEX: keywords="openscad, 3d_parametric, Galatian_Star_Keyring, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Galatian Star Keyring

// ===== file: GalatianStar2.scad =====
include <keyring.scad>;

module galatianstar(outer, inner, height)
{

	function side_from_diag(di) = sqrt(pow(di,2)/2);
	dimensions = [side_from_diag(outer), side_from_diag(outer), height];
	d2 = [side_from_diag(inner), side_from_diag(inner), height];

	module star(dimensions, height){
		cube(dimensions, center=true);
		rotate(45, 0) cube(dimensions, center=true);
		translate([(outer/2+1.5),0,0]) keyring(3,5,height);
	}

	difference(){
		star(dimensions, height);
		translate([0,0,(height/2)]) star(d2, height);
	}
	translate([(outer/2+1.5),0,0]) keyring(3,5,height);
}



galatianstar(30, 25,3);





// ===== file: keyring.scad =====
module keyring(inner, outer, thickness){

	difference(){
		cylinder(thickness, outer/2, outer/2, center=true, $fs=0.2);
		cylinder(thickness*2, inner/2, inner/2, center=true, $fs=0.2);
	}
}
