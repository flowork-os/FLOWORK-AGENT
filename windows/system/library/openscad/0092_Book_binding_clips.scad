// [FL_INDEX: keywords="openscad, 3d_parametric, Book_binding_clips, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Book binding clips

//book thickness (mm)
thickness = 19.4;

cube(size=[thickness,3,10]);
translate([-3,0,0])
cube(size=[3,15,10]);
translate([thickness,0,0])
cube(size=[3,15,10]);