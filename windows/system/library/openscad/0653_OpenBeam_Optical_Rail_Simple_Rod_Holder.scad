// [FL_INDEX: keywords="openscad, 3d_parametric, OpenBeam_Optical_Rail_Simple_Rod_Holder, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: OpenBeam Optical Rail Simple Rod Holder

// The base for  the open optics rail made from Open Beam
// holds a 13mm smooth rod


//Variables
w=15; //Width of Open Beam
d=9; // rod diameter
x =6.5; //width of screw head
g =2; //heigth of screw head with some margin
z =4; //width of screw thread with margin
i=2; //screw heigth
a=20; //total heigth

module base(){
				difference(){
			difference(){
		difference (){
		cylinder(a, w/2,w/2);//whole chuck
		cylinder(a-g*2,d/2,d/2); //magnet hole
				}
			cylinder(a,z/2,z/2); //screw hole	
					}
				translate ([0,0,a-g-2])
				cylinder(g,x/2,x/2); //head of screw hole
						}
		}

base();