// [FL_INDEX: keywords="openscad, 3d_parametric, Dixon_Ticonderoga_Pencil_Clip, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Dixon Ticonderoga Pencil Clip

include <MCAD/shapes.scad>
use <write.scad> 
pencilRadius = 7/2;
wallThickness = 3;
pencilWall = pencilRadius + wallThickness;
height = 38;
length = 35;

difference() {
union() {
cylinder(height,pencilWall,pencilWall,true);
difference () {
translate([-2,-length/2,0])
cube([wallThickness,length,height],true);
translate ([-4,-30,-15]) rotate ([90,0,90]) write("I",h=30,t=2,font="orbitron.dxf");
}
difference () {
translate([2,-length/2,0])
cube([wallThickness,length,height],true);
rotate ([90,90,90]) translate ([-12,-30,2]) write(":)",h=22,t=3,space=.7,font="orbitron.dxf");
}

}

//#cylinder(height+2,pencilRadius,pencilRadius,true);
#hexagon(pencilRadius*2, height+2);



}
translate([3.1,-(length+(wallThickness*0.5)),0])
cylinder(height,wallThickness,wallThickness,true);
translate([-3.1,-(length+(wallThickness*0.5)),0])
cylinder(height,wallThickness,wallThickness,true);




