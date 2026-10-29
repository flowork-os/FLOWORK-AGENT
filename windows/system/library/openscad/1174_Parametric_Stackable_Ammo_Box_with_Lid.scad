// [FL_INDEX: keywords="openscad, 3d_parametric, Parametric_Stackable_Ammo_Box_with_Lid, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Parametric Stackable Ammo Box with Lid

//Rows of casings
rows = 5;

//Colums of casings
columns = 8;

//Height of the holes in mm
height = 78;


//Diameter of the holes in mm
space= 12.8;

//Wall thickness between holes in mm
wall = 2.5;
//Outerwall additional thickness
oWall = 1;

//renderoptions
both = true;
box = false;

if(both){
	box();
	lid();
}

if(!both){
	if(box){
		box();
		}
	if(!box){
		lid();
		}
}
module box(){
difference(){
	//Main case cube
union(){
	cube([(wall + space) * columns + wall + 2 * oWall+10,(wall + space) *rows + wall + 2 * oWall+10, height]);
translate([4,4,height]){
cube([(wall + space) * columns + wall + 2 * oWall+2,(wall + space) *rows + wall + 2 * oWall+2, 4]);
}
}
	for(r=[0:rows-1]){
		for(c=[0:columns-1]){
			//Inner Hollow Top
			# translate ([c*(space+wall)+wall+oWall+space/2+5,r*(space+wall)+wall+oWall+space/2+5,4]) {
				cylinder(h = height, r=space/2);
			}
		
		}
	}
translate([6,6,height]){
cube([(wall + space) * columns + wall + 2 * oWall-2,(wall + space) *rows + wall + 2 * oWall-2, 4]);}
}}

module lid(){
translate([0,-(space * rows +  rows * wall * 3),0]){	
difference(){
	cube([(wall + space) * columns + wall + 2 * oWall+10,(wall + space) *rows + wall + 2 * oWall+10, 10]);
translate([4,4,4]){
cube([(wall + space) * columns + wall + 2 * oWall+2,(wall + space) *rows + wall + 2 * oWall+2, 8]);}
}
}
}
