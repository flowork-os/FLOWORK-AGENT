// [FL_INDEX: keywords="openscad, 3d_parametric, Solidoodle_Torsional_Anti-Backlash_Nut_for_Z-Axis, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Solidoodle Torsional Anti-Backlash Nut for Z-Axis

// preview[view:south, tilt:top]

/* [Adjustments] */

base_plate_screw_diameter = 2.5;

base_plate_screw_head_thickness = 1.0;

base_plate_thickness = 2.5;

// Distance between base plate screws in x-axis
x_axis_seperation = 25.4;

// Distance between base plate screws in y-axis
y_axis_seperation = 15.875;

// Width across flats
nut_width = 12.7;

nut_height = 6.8;

// Should be larger than outer diameter of lead screw
lead_screw_hole_diameter = 8.0;

extra_height = 1;

spring_wire_diameter = 1.0;

//(mm)
tolerance = 0.4;

/* [Hidden] */

include <MCAD/regular_shapes.scad>

base_plate_perimeter_buffer = 3.0;

nut_width_across_corners = nut_width / cos(30);
base_plate_screw_radius = base_plate_screw_diameter / 2;
base_plate_corner_radius = base_plate_perimeter_buffer + base_plate_screw_radius;
base_plate_width = x_axis_seperation + base_plate_corner_radius * 2;
base_plate_depth = y_axis_seperation + base_plate_corner_radius * 2;
collar_height = 2;
top_plate_thickness = 2.0;
spring_restraint_radius = ((nut_width_across_corners/2)+1.5+spring_wire_diameter+1.6);
spring_section_radius = (nut_width_across_corners/2)+1.5;


//Base
difference() {
	union() {
		//Base plate
		translate([0,0,base_plate_thickness/2])
			difference() {
				union() {
					cube(size=[base_plate_width,y_axis_seperation,base_plate_thickness],center=true);
					cube(size=[x_axis_seperation,base_plate_depth,base_plate_thickness],center=true);
					for (i = [[1,1],[1,-1],[-1,-1],[-1,1]]) {
						translate([x_axis_seperation*i[0]/2,y_axis_seperation*i[1]/2,0])
							cylinder(h=base_plate_thickness,r=base_plate_corner_radius,center=true,$fs=1);
					}
				}
				for (i = [[1,1],[1,-1],[-1,-1],[-1,1]]) {
					translate([x_axis_seperation*i[0]/2,y_axis_seperation*i[1]/2,0])
						cylinder(h=base_plate_thickness,r=(base_plate_screw_radius+tolerance),center=true,$fs=1);
				}
			}
		//Spring restraint collar
		translate([0,0,(base_plate_thickness)])
			for (i=[0:5]) {
				rotate ([0,0,60*i-	15])
					arc((collar_height+base_plate_screw_head_thickness+tolerance),spring_restraint_radius,spring_restraint_radius,(30-atan(tolerance*2/spring_restraint_radius)));
			}
		//Spring section
		cylinder(h=(base_plate_thickness+nut_height+2+extra_height),r=(spring_section_radius-tolerance/2),center=false,$fs=1);
	}
	//Nut trap
	linear_extrude(height=(nut_height),center=false)
		circle(r=(nut_width_across_corners/2+tolerance/2),$fn=6);
	//Lead screw hole
	cylinder(h=(nut_height*2+3),r=((lead_screw_hole_diameter+tolerance*2)/2),center=false,$fs=1);
}

//Base support
cylinder_tube(nut_height-0.3,lead_screw_hole_diameter/2+1+tolerance,1);


//Upper
translate([0,((base_plate_depth/2)+((nut_width_across_corners/2)+3+spring_wire_diameter+1.4)+5),0])
	difference() {
		//Main body
		union() {
			cylinder(h=top_plate_thickness,r=(spring_restraint_radius+0.8),center=false,$fs=1);
			cylinder(h=(nut_height+2),r=(spring_section_radius-tolerance/2),center=false,$fs=1);
		}
		//Lead screw hole
		cylinder(h=(nut_height+3),r=((lead_screw_hole_diameter+tolerance*2)/2),center=false,$fs=1);
		//Nut trap
		linear_extrude(height=nut_height,center=false)
			circle(r=(nut_width_across_corners/2+tolerance/2),$fn=6);
		//Spring hole
		translate([(spring_restraint_radius-(spring_wire_diameter+1.6)/2),0,0])
			cylinder(h=top_plate_thickness,r=(((spring_wire_diameter)/2)+tolerance/2),center=false,$fs=0.1);
	}

//Upper support
translate([0,((base_plate_depth/2)+((nut_width_across_corners/2)+3+spring_wire_diameter+1.4)+5),0])
  cylinder_tube(nut_height-0.3,lead_screw_hole_diameter/2+1+tolerance,1);


//Spring restraint collar
translate([((base_plate_width/2)+((nut_width_across_corners/2)+3+spring_wire_diameter+1.4)+5),0,0])
	difference() {
		//Main body
		union() {
			difference() {
				cylinder(h=collar_height,r=(spring_restraint_radius+tolerance/2),center=false,$fs=1);
				cylinder(h=collar_height,r=(spring_section_radius+tolerance/2),center=false,$fs=1);
			}
			translate([0,0,(collar_height)])
				for (i=[0:5]) {
					rotate ([0,0,60*i])
						arc(collar_height,(spring_wire_diameter+1.6),(spring_restraint_radius+tolerance/2),30);
				}
		}
		//Spring hole
	    rotate ([0,0,15])
	  		translate([spring_restraint_radius+(tolerance/2)-(spring_wire_diameter+1.6)/2,0,0])
	        	cylinder(h=(collar_height*2),r=((spring_wire_diameter/2)+tolerance/2),center=false,$fs=0.1);
	};



// ----------------------------------------------------------------------------
//include module to generate arcs/wedges
module arc( height, depth, radius, degrees ) {
    // This dies a horible death if it's not rendered here 
    // -- sucks up all memory and spins out of control 
    render() {
        difference() {
            // Outer ring
            rotate_extrude($fs = 1)
                translate([radius - depth, 0, 0])
                    square([depth,height]);
         
            // Cut half off
            translate([0,-(radius+1),-.5]) 
                cube ([radius+1,(radius+1)*2,height+1]);
         
            // Cover the other half as necessary
            rotate([0,0,180-degrees])
            translate([0,-(radius+1),-.5]) 
                cube ([radius+1,(radius+1)*2,height+1]);
         
        }
    }
}