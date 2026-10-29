// [FL_INDEX: keywords="openscad, 3d_parametric, Customizeable_RC_Plane_Wheel_Hangers, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizeable RC Plane Wheel Hangers

//left, right, or both holders?
part="both"; 							//[left,right,both]

//mm Diameter of the wheels
diameter = 50; 	

//mm total width of wheel + horizontal portion of axle					
width=30; 	
					
//mm diameter of nail/screw you will be using		
nail_diameter=2.7; 					

//will your nail/screw be angled or horizontal?
nail_orientation="angled"; 		//[horizontal,angled]

//mm Clearance space to allow wheel to fit in slot
tolerance=5; 							

//mm Slot for axle to slide through (width of axle + extra space)
axle_clearance=10; 					

//do not edit this parameter at the moment
wall_thickness=5;
print_part();

module print_part() {
	if (part == "left") {
		left();
	} else if (part == "right") {
		right();
	} else if (part == "both") {
		both();
	} else {
		both();
	}
}

module both(){
	translate([(width+2*wall_thickness+tolerance+10)/2,0,0])right();
	translate([-(width+2*wall_thickness+tolerance+10)/2,0,0])left();
}
module right(){
difference(){

union(){
		cube([width+2*wall_thickness+tolerance,diameter+2*wall_thickness+tolerance,diameter+2*wall_thickness+tolerance]);

		translate([0,diameter+2*wall_thickness+tolerance,0])
		cube([width+2*wall_thickness+tolerance,5,diameter+2*wall_thickness+tolerance+25]);
}

translate([width/2+wall_thickness+tolerance/2,diameter/2+wall_thickness+tolerance/2,diameter/2+wall_thickness+tolerance/2])
rotate([90, 0, 90])
cylinder(h = width+tolerance, r=diameter/2+tolerance/2,$fn=100,center=true);	

translate([wall_thickness,wall_thickness,diameter/2+wall_thickness+tolerance/2])
cube([width+tolerance,diameter+tolerance,diameter+tolerance*5]);	


translate([wall_thickness,-1,diameter/2+wall_thickness+tolerance/2])
cube([axle_clearance,diameter/2,diameter]);	





if(nail_orientation=="angled"){
	translate([width/2+wall_thickness+tolerance/2,diameter+2*wall_thickness+tolerance,diameter+2*wall_thickness+tolerance+25/2])
	rotate([45, 0, 0])
	cylinder(h = 500, r=nail_diam/2,$fn=100,center=true);	
}
else{
	translate([width/2+wall_thickness+tolerance/2,diameter+2*wall_thickness+tolerance,diameter+2*wall_thickness+tolerance+25/2])
	rotate([90, 0, 0])
	cylinder(h = 500, r=nail_diam/2,$fn=100,center=true);	
}

}
}

module left(){
difference(){

union(){
		cube([width+2*wall_thickness+tolerance,diameter+2*wall_thickness+tolerance,diameter+2*wall_thickness+tolerance]);

		translate([0,diameter+2*wall_thickness+tolerance,0])
		cube([width+2*wall_thickness+tolerance,5,diameter+2*wall_thickness+tolerance+25]);
}

translate([width/2+wall_thickness+tolerance/2,diameter/2+wall_thickness+tolerance/2,diameter/2+wall_thickness+tolerance/2])
rotate([90, 0, 90])
cylinder(h = width+tolerance, r=diameter/2+tolerance/2,$fn=100,center=true);	

translate([wall_thickness,wall_thickness,diameter/2+wall_thickness+tolerance/2])
cube([width+tolerance,diameter+tolerance,diameter+tolerance*5]);	


translate([width-wall_thickness+tolerance,-1,diameter/2+wall_thickness+tolerance/2])
cube([axle_clearance,diameter/2,diameter]);	





if(nail_orientation=="angled"){
	translate([width/2+wall_thickness+tolerance/2,diameter+2*wall_thickness+tolerance,diameter+2*wall_thickness+tolerance+25/2])
	rotate([45, 0, 0])
	cylinder(h = 500, r=nail_diam/2,$fn=100,center=true);	
}
else{
	translate([width/2+wall_thickness+tolerance/2,diameter+2*wall_thickness+tolerance,diameter+2*wall_thickness+tolerance+25/2])
	rotate([90, 0, 0])
	cylinder(h = 500, r=nail_diam/2,$fn=100,center=true);	
}

}
}