// [FL_INDEX: keywords="openscad, 3d_parametric, Single_Wall_Cylinder__customizer, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Single Wall Cylinder (customizer)

//Diameter of cylinder
diameter=30;
//Width of single wall layer
extrusionWidth=0.55;
//Height of cylinder
height=8;
//Height/thickness of bottom (0 for no bottom)
layerHeight=0.2;


/* [hidden] */
rad=diameter/2;
$fn=200;

union() {
translate([0,0,-layerHeight]) cylinder(r=rad, h=layerHeight);
	difference () {
		cylinder(r=rad, h=height);
		translate([0,0,-1])
		cylinder(r=rad-extrusionWidth, h=height+2);
	}
}