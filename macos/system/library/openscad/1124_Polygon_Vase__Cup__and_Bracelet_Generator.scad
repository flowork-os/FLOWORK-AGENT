// [FL_INDEX: keywords="openscad, 3d_parametric, Polygon_Vase__Cup__and_Bracelet_Generator, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Polygon Vase, Cup, and Bracelet Generator

//Top Diameter in mm
t2=60;  // [5:200]
t=t2/2;

//Middle Diameter
m2=80; // [5:200]
m=m2/2;

//Base Diameter
b2=50; // [5:200]
b=b2/2;

//Vase Height
h=70; // [5:200]

//How many layers should there be?
layers=100; // [5:800]

//How many degrees should each layer rotate?
r=.5; // Best with small numbers

//Make a double spiral?
d="Yes"; // [Yes, No]

//Size of surface features in degrees
smoothness=30; // [1:90]

//Force hollow?
fh="No"; // [No, Vase, Bracelet]

/*[Hidden]*/
angle = 90;
layersq=layers*layers/4;
$fa=smoothness;
floor=2/(h/layers);

for (i=[0:layers]) {
	if (fh=="No") {
		translate([0,0,i/layers*h]) rotate([0,0,r*i+angle]) cylinder(r=b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m),h=h/layers*1.1,center=true);
		if (d=="Yes") {
		translate([0,0,i/layers*h]) rotate([0,0,-(r*i+angle)]) cylinder(r=b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m),h=h/layers*1.1,center=true);
		}
	}
	if (fh=="Bracelet") {
		difference() {
			union() {
				translate([0,0,i/layers*h]) rotate([0,0,r*i+angle]) cylinder(r=b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m),h=h/layers*1.1,center=true);
				if (d=="Yes") {
				translate([0,0,i/layers*h]) rotate([0,0,-(r*i+angle)]) cylinder(r=b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m),h=h/layers*1.1,center=true);
				}
			}
			translate([0,0,i/layers*h]) rotate([0,0,r*i+angle]) cylinder(r=b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m)-2,h=h/layers*1.2,center=true);
			if (d=="Yes") {
			translate([0,0,i/layers*h]) rotate([0,0,-(r*i+angle)]) cylinder(r=b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m)-2,h=h/layers*1.2,center=true);
			}
		}
	}
	if (fh=="Vase") {
		difference() {
			union() {
				translate([0,0,i/layers*h]) rotate([0,0,r*i+angle]) cylinder(r=b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m),h=h/layers*1.1,center=true);
				if (d=="Yes") {
				translate([0,0,i/layers*h]) rotate([0,0,-(r*i+angle)]) cylinder(r=b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m),h=h/layers*1.1,center=true);
				}
			}
			if (i>floor) {			
				translate([0,0,i/layers*h]) rotate([0,0,r*i+angle]) cylinder(r=b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m)-2,h=h/layers*1.2,center=true);
				if (d=="Yes") {
				translate([0,0,i/layers*h]) rotate([0,0,-(r*i+angle)]) cylinder(r=b+i/layers*(t-b)+((i-layers/2)*(i-layers/2)-layersq)/layersq*((b+t)/2-m)-2,h=h/layers*1.2,center=true);
				}
			}
		}
	}

}