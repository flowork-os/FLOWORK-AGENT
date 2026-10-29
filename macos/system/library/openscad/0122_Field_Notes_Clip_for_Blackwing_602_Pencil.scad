// [FL_INDEX: keywords="openscad, 3d_parametric, Field_Notes_Clip_for_Blackwing_602_Pencil, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Field Notes Clip for Blackwing 602 Pencil

include <MCAD/shapes.scad>
pencilRadius = 4.1;
wallThickness = 3;
pencilWall = pencilRadius + wallThickness;
height = 38;
length = 35;

difference() {
union() {
cylinder(height,pencilWall,pencilWall,true);
translate([-3.75,-length/2,0])
cube([wallThickness,length,height],true);
translate([3.75,-length/2,0])
cube([wallThickness,length,height],true);
}

//#cylinder(height+2,pencilRadius,pencilRadius,true);
#hexagon(pencilRadius*2, height+2);



}
translate([3.75,-(length+(wallThickness*0.5)),0])
cylinder(height,wallThickness,wallThickness,true);
translate([-3.75,-(length+(wallThickness*0.5)),0])
cylinder(height,wallThickness,wallThickness,true);