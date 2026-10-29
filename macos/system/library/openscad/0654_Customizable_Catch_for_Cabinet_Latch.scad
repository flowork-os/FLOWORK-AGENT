// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_Catch_for_Cabinet_Latch, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable Catch for Cabinet Latch

/****************************************************/
/*************User specified parameters**************/

//length of catch base
length = 40; // [5:100]

//width of catch base
width = 11; // [5:100]

//maximum height of catch
height = 11; // [5:100]

//thickness of catch base
base_thick = 2; // [0.25:5]

//width of flat portion at the top of catch
top_width = 2; // [0.25:5]

//the length (along the long axis) of the curved portion of the catch
curve_length = 19; // [5:100]

//max deviation of curve from a straight line. Place straight edge against curve, and find the max gap.
sag = 1.5; // [0.25:5]

//center to center spacing of holes
hole_spacing = 32; // [5:100]

//wide axis of hole
hole_length = 9; // [5:100]

//narrow axis of hole
hole_width = 3.75; // [0.25:5]

//fudge factor to ensure overlaps
wiggle = 0.1; // [0.001,0.01,0.1]

$fn=10;
/****************************************************/

/***************Calculated parameters****************/
curve_height = height - base_thick; // height of curved portion of catch
curve_width = width - top_width; // width of curved portion of catch
curve_chord_length = sqrt(pow(curve_height,2) + pow(curve_width,2)); // length of the chord connecting the uppermost and lowermost points on the curve
R = (pow(curve_chord_length/2,2)+pow(sag,2))/(2*sag); // Radius of the curve
ratio = curve_height/curve_width; // calculated parameter to make algebra easier
A = 1 + pow(ratio,2); // first coefficient of y quadratic equation
B = curve_height; // second coefficient of y quadratic equation
C = pow(curve_width,2)*A/4-pow(R,2)/A; // third coefficient of y quadratic equation
y = (-B + sqrt(pow(B,2) - 4*C))/2; // vertical distance from top of catch to the center of curvature
x = curve_width*(pow(ratio,2) - 1)/2 + ratio*y; // horizontal distance from top of catch to the center of curvature
echo (str("R = ",R));
echo (str("x = ",x));
echo (str("y = ",y));
echo (str("ratio = ",ratio));
echo (str("discriminant = ",pow(B,2) - 4*A*C));
/****************************************************/

union(){	
	difference(){
		cube([length,width,base_thick]);
		for (i=[-1,1]){
			translate([length/2 + i*hole_spacing/2,(width - hole_length + hole_width)/2,-wiggle]) #screwhole();
		}
	}
	
	difference(){
		translate([(length-curve_length)/2,0,base_thick]) cube([curve_length,width,curve_height]);
		#translate([(length-curve_length)/2-wiggle,width + x,height + y]) rotate([0,90,0]) cylinder(h=curve_length+2*wiggle,r=R,center=false,$fn=50);
	}
}


module screwhole()
{
	hull(){
		cylinder(h=base_thick+2*wiggle,r=hole_width/2,center=false);
		translate([0,5.25,0]) cylinder(h=base_thick+2*wiggle,r=hole_width/2,center=false);
	}
}
