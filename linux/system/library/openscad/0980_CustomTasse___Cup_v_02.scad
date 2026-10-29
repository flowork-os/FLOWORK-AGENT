// [FL_INDEX: keywords="openscad, 3d_parametric, CustomTasse___Cup_v_02, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: CustomTasse / Cup v.02

// CustomTasse / Cup v.03
// My first openScad Test
// onlyjonas, 2013-05-4

//cup height 
tasseH = 90;
//cup radius
tasseR = 25;
//wall thickness 
tasseWand = 3;
//handle type
henkelType = 2; //[1, 2]
//handle radius
henkelR = 15;
//handle thickness
henkelDicke = 4;
//handle position in percentage
henkelPosition = 90; //[0:100]

module henkelA(henkelPos)
{
	translate([tasseR+henkelR-10,0,henkelPos])
	rotate([90,0,0]) 
	rotate_extrude(convexity = 10, $fn = 360)
	translate([henkelR, 0, 0])
	circle(henkelDicke);
}

module henkelB(henkelPos)
{	
	translate([tasseR+henkelR,0,henkelPos])
	rotate([-90,90,0]) 
	linear_extrude(height = henkelDicke){
	difference() {
	
		union(){
			circle(henkelR, $fn = 360);
			translate([0, henkelR , 0]) square([henkelR*2, henkelR*2], center=true);
		}

		circle(henkelR-henkelDicke, $fn = 360);
	}
	};	
}

module henkel()
{
	pos = ((tasseH-henkelR*2)*henkelPosition/100)+henkelR;

	if (henkelType==1) henkelA(pos);
	if (henkelType==2) henkelB(pos);
}

module tasse()
{

	difference() {
		union() {
		cylinder(h = tasseH, r = tasseR, $fn = 360);
		henkel();
		}
		translate([0,0,tasseWand]) 
		cylinder(h = tasseH+tasseWand, r = tasseR-tasseWand, $fn = 360);
		
	}
}

tasse();