// [FL_INDEX: keywords="openscad, 3d_parametric, Simple_Customizable_Ring_Stand, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Simple Customizable Ring Stand

extremes=80;
LegLength=60;
LegWidth=10;
Thickness=3;
LegSpacing=40;
strutwidth=5;
height=40;
probeRadius=5;
screwRadius=1;

intersection(){
	cube(extremes);
	difference(){
		union(){
			cube([LegLength,LegWidth,Thickness]);
			translate([0,LegSpacing+LegWidth,0])cube([LegLength,LegWidth,Thickness]);
			hull(){
				translate([0,LegSpacing+LegWidth,0])cube([Thickness,LegWidth,Thickness]);
				translate([0,(LegSpacing+LegWidth)/2+strutwidth,height])rotate([0,90,0])cylinder(r=strutwidth,h=Thickness);
			}
			hull(){
				translate([0,0,0])cube([Thickness,LegWidth,Thickness]);
				translate([0,(LegSpacing+LegWidth)/2+strutwidth,height])rotate([0,90,0])cylinder(r=strutwidth,h=Thickness);
			}
			translate([0,(LegSpacing+LegWidth)/2,height-Thickness])cube([LegLength*.75,LegWidth,Thickness]);
			translate([0,(LegSpacing+LegWidth)/2+strutwidth-Thickness/2,height-Thickness/2])rotate([0,90,90])cylinder(r=strutwidth+Thickness/2,h=Thickness);
			translate([LegLength*.75,(LegSpacing+LegWidth)/2+probeRadius,height-2*Thickness])cylinder(r=probeRadius+Thickness,h=3*Thickness);
		}
		translate([LegLength*.75,(LegSpacing+LegWidth)/2+probeRadius,height-2*Thickness])cylinder(r=probeRadius,h=7*Thickness);
		translate([LegLength*.75+probeRadius-Thickness,(LegSpacing+LegWidth)/2+probeRadius,height-.5*Thickness])rotate([0,90,0])cylinder(r=screwRadius,h=7*Thickness);
	}
}
