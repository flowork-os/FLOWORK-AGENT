// [FL_INDEX: keywords="openscad, 3d_parametric, Rounded_Square_Vase__Cup__and_Bracelet_Generator, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Rounded Square Vase, Cup, and Bracelet Generator

//Top Diameter in mm
t=45;  // [5:200]

//Middle Diameter
m=55; // [5:200]

//Base Diameter
b=30; // [5:200]

//Vase Height
h=80; // [5:200]

//How many layers should there be?
layers=90; // [5:200]

//How many degrees should each layer rotate?
r=1; // Best with small numbers

//Radius of curved edge
ps=10; //[0:10]

//How many squares should be in each layer?
points = 1; // [1:20]

//Make a double spiral?
d="Yes"; // [Yes, No]

angle = 90/points;
layersq=layers*layers/4;

for (i=[0:layers]) {
	for (j=[1:points]) {
		translate([0,0,i/layers*h]) rotate([0,0,r*i+angle*j]) 
		minkowski (){
			cube([b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m),b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m),h/layers*1.01],center=true);
			cylinder(r=ps,h=1,$fs=0.5);
		}
		if (d=="Yes") {
			translate([0,0,i/layers*h]) rotate([0,0,-(r*i+angle*j)]) 
			minkowski (){
				cube([b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m),b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m),h/layers*1.01],center=true);
				cylinder(r=ps,h=1,$fs=0.5);
			}
		}
	}
}