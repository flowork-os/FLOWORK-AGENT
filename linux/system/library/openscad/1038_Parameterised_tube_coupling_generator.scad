// [FL_INDEX: keywords="openscad, 3d_parametric, Parameterised_tube_coupling_generator, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Parameterised tube coupling generator

//Parameterised coupling generator
// Glyn Cowles Mar/Apr 2013


//Thickness of tube walls 
thickness=1.5; 
//Outside diameter of bottom tube 
d1=69;   
//Height of bottom tube 
h1=5;   
//Outside diameter of top tube
d2=90;   
//Height of top tube
h2=10;   
//Height of connector section
c_ht=25; 
// resolution
$fn=90;
assemble(); 
//-----------------------------------------------------------------------
module tube(d,h) {
rad=d/2;
difference() {
cylinder(h=h,r=rad);
cylinder(h=h,r=rad-thickness);
}
}
//-----------------------------------------------------------------------

module connector(){
difference() {
 cylinder (h=c_ht,r1=d1/2,r2=d2/2);
 cylinder (h=c_ht,r1=d1/2-thickness,r2=d2/2-thickness);
}
}

module assemble() {
union() {
	tube(d1,h1);
	translate([0,0,h1]) connector(); 
	translate([0,0,h1+c_ht])  tube(d2,h2);
	}
};



