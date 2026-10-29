// [FL_INDEX: keywords="openscad, 3d_parametric, Rocket, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Rocket

$fn=100*1;


//height
numerical_slider_1 =  80;//[60:1000]

//diameter
numerical_slider_2 =  6;//[2:100]

//scale_wings %
scale_wings=100;//[50:3000]

//scale_model %
scale_model=100;

difference() {
union() {
scale([scale_model/100,scale_model/100,scale_model/100]) {
cylinder(h=numerical_slider_1, r=numerical_slider_2);
translate([0,0,numerical_slider_1]) scale([1,1,7]) sphere(numerical_slider_2);

for (i = [0:3]){ 
		rotate([0,0,i*360/4])
			translate([0,(0.5*scale_wings)/100,0]) {
				rotate([90,0,0]) {
					scale([scale_wings/100,scale_wings/100,scale_wings/100]) {
						linear_extrude(height=1) {
							polygon(points=[[0,0],[20,0],[0,30]]);
}
}
}
}
}
}
}
translate([0,0,-100*numerical_slider_2*scale_wings*scale_model]) cylinder(h=100*numerical_slider_2*scale_wings*scale_model, r=100*numerical_slider_2*scale_wings*scale_model);
}