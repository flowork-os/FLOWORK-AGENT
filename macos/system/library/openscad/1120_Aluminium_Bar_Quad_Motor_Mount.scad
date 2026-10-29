// [FL_INDEX: keywords="openscad, 3d_parametric, Aluminium_Bar_Quad_Motor_Mount, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Aluminium Bar Quad Motor Mount

tube_thickness=20.2;
support_wall_thickness=3;
plate_diameter=42.5;
difference(){
cylinder(r=(plate_diameter/2),h=13,$fn=60);
translate([-10,-plate_diameter/2,3]) cube([tube_thickness,plate_diameter,20],centre=true);
translate([-(plate_diameter/2),-plate_diameter/2,3]) cube([((plate_diameter/2)-(tube_thickness/2+support_wall_thickness)),plate_diameter,20]);
translate([((plate_diameter/2)-((plate_diameter/2)-(tube_thickness/2+support_wall_thickness))),-plate_diameter/2,3]) cube([((plate_diameter/2)-(tube_thickness/2+support_wall_thickness)),plate_diameter,20]);
//mounting holes //
translate([0,-(42.5/2)+4.8,0]) cylinder(r=1.7,h=3,$fn=60);
translate([0,(42.5/2)-4.8,0]) cylinder(r=1.7,h=3,$fn=60);
translate([-(42.5/2)+4.8,0,0]) cylinder(r=1.7,h=3,$fn=60);
translate([(42.5/2)-4.8,0,0]) cylinder(r=1.7,h=3,$fn=60);
}

