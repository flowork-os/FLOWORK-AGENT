// [FL_INDEX: keywords="openscad, 3d_parametric, o-ringer__create_your_own_o-rings, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: o-ringer (create your own o-rings)

// This generates o-rings
// Licenced under Creative Commons: Attribution, Share-Alike
//		http://creativecommons.org/licenses/by-sa/3.0/
// For attribution you can direct people to the original file on thingiverse:
// 		http://www.thingiverse.com/thing:225603
//
// For more than you ever wanted to know about O-rings, check out:
//		http://www.allsealsinc.com/ParcoO-RingSizeChart.pdf

// ================ variables

//CUSTOMIZER VARIABLES

/* [Main] */

// What do you want to create?
goal=0; // [0:"the o-ring itsself",1:"o-ring mold bottom",2:"o-ring mold top"]

// What units your measurements are in (experimental)
units=0; // [0:"mm",1:"cm",2:"in",3:"thou"]

// Please specify this and cross sectional diameter OR inside diameter NOT BOTH
outside_diameter=40;

// Please specify this OR inside diameter NOT BOTH
cross_sectional_diameter=3;

// Please specify this OR cross sectional diameter NOT BOTH
inside_diameter=-1;

// Lengthen the o ring along the z axis this much more. This is to prevent "rubber band" curling when in use.  (May mess up "undersizing" slightly when both are used.)
minionizing_cross_section=0;

// Make the o-ring diameter this much (in selected units) undersized. This is different than changing the id/od because it also accounts for streach volume.
undersizing=0;

// Level of detail. (Cranking this up makes a nice model, but makes rendering very slow!)
$fn=60; // [30:150]

/* [Mold settings] */

// How thick(mm) the walls arount the part are.
mold_perimeter=5;

// The size(mm) of the mold fill/vent holes.
mold_hole_size=4;

// The height(mm) of the inlet riser for the top mold.
riser_height=15;

// The inlet size(mm). Increase for more viscous rubber, decrease for less cleanup.
sprue_thickness=0.5;

//CUSTOMIZER VARIABLES END
module dummy() {};

// =============== program

// ---- Data
units_names=["mm","cm","in","thou"];
units_conversion=[1.0,10.0,25.4,0.0254];

//---- Functions

// converts using the global "units" value or whatever is specified
function tomm(u,t_units=-1) = u*units_conversion[t_units<0?units:t_units];
function fn_inside_diameter(inside_diameter,outside_diameter,cross_sectional_diameter) = ((inside_diameter>0)?(inside_diameter):(outside_diameter-(cross_sectional_diameter/2)));
function fn_cross_sectional_diameter(inside_diameter,outside_diameter,cross_sectional_diameter) = ((inside_diameter>0)?((outside_diameter-inside_diameter)*2):(cross_sectional_diameter));

/////////////////////////////////////////////////////////
// module _o_ring_B()
// actually generates the geometry
// use create_o_ring instead.  This is just a helper.
/////////////////////////////////////////////////////////
module _o_ring_B (outside_diameter=40,cross_sectional_diameter=3,minionizing_cross_section=0) {
	echo(str("final cross_sectional_diameter=",cross_sectional_diameter));
	rotate_extrude() translate([(outside_diameter-(cross_sectional_diameter/2))/2,0,0]) if (minionizing_cross_section>0) {
		union() {
			translate([0,minionizing_cross_section/2,0]) circle(r=cross_sectional_diameter/2);
			square([cross_sectional_diameter,minionizing_cross_section],center=true);
			translate([0,-minionizing_cross_section/2,0]) circle(r=cross_sectional_diameter/2);
		}
	} else {
		circle(r=cross_sectional_diameter/2);
	}
};

/////////////////////////////////////////////////////////
// module _o_ring_A()
// accounts for undersizing using delta-volume between stretched and relaxed state
// use create_o_ring instead.  This is just a helper.
/////////////////////////////////////////////////////////
module _o_ring_A (outside_diameter=40,cross_sectional_diameter=3,minionizing_cross_section=0,undersizing=0) {
		if(undersizing>0) {
			// Hint: volume of a torus is 2*PI^2*R*r^2
			// So for the same volume, that means: R1*r1^2=R2*r2^2
			// or, r2=sqrt(R1*r1^2/R2)
			echo(str("cross_sectional_diameter=",cross_sectional_diameter));
			_o_ring_B(outside_diameter-undersizing,
				2*sqrt(
					(((outside_diameter-(cross_sectional_diameter)/2)/2)
					*
					pow(cross_sectional_diameter/2,2))
					/
					(((outside_diameter-undersizing)-(cross_sectional_diameter)/2)/2)
				),minionizing_cross_section);
		}else{
			_o_ring_B(outside_diameter,cross_sectional_diameter,minionizing_cross_section);
		}
};

/////////////////////////////////////////////////////////
// module create_o_ring()
// units - Whether you are measuring is mm or .thou
// outside_diameter - Please specify this and cross sectional diameter OR inside diameter NOT BOTH
// cross_sectional_diameter - Please specify this OR inside diameter NOT BOTH
// inside_diameter - Please specify this OR cross sectional diameter NOT BOTH
// minionizing_cross_section - This is used for widening the o ring along the z axis to prevent twisting
// undersizing - Make the o-ring diameter this much undersize (this is different than changing the id/od because it also accounts for streach volume)
/////////////////////////////////////////////////////////
module create_o_ring (units=0,outside_diameter=40,cross_sectional_diameter=3,inside_diameter=-1,minionizing_cross_section=0,undersizing=0) {
		if(inside_diameter>0) {
			_o_ring_A(tomm(outside_diameter,units),tomm((outside_diameter-inside_diameter)/2,units),tomm(minionizing_cross_section,units),tomm(undersizing,units));
		}else{
			_o_ring_A(tomm(outside_diameter,units),tomm(cross_sectional_diameter,units),tomm(minionizing_cross_section,units),tomm(undersizing,units));
		}
};

/////////////////////////////////////////////////////////
// module o_ringer()
// same as create_o_ring() but adds the ability to create molds
// goal - [0:"the o-ring itsself",1:"o-ring mold bottom",2:"o-ring mold top"]
// units - Whether you are measuring is mm or .thou
// outside_diameter - Please specify this and cross sectional diameter OR inside diameter NOT BOTH
// cross_sectional_diameter - Please specify this OR inside diameter NOT BOTH
// inside_diameter - Please specify this OR cross sectional diameter NOT BOTH
// minionizing_cross_section - This is used for widening the o ring along the z axis to prevent twisting
// undersizing - Make the o-ring diameter this much undersize (this is different than changing the id/od because it also accounts for streach volume)
// mold_perimeter - How thick(mm) the walls arount the part are.
// mold_hole_size - The size(mm) of the mold fill/vent holes.
// riser_height - The height(mm) of the inlet riser for the top mold.
// sprue_thickness - The inlet size(mm). Increase for more viscous rubber, decrease for less cleanup.
/////////////////////////////////////////////////////////
module o_ringer(goal=0,units=0,outside_diameter=40,cross_sectional_diameter=3,inside_diameter=-1,minionizing_cross_section=0,undersizing=0,mold_perimeter=5,mold_hole_size=4,riser_height=15,sprue_thickness=0.5)
{
	if(goal==0){
		create_o_ring(units,outside_diameter,cross_sectional_diameter,inside_diameter,minionizing_cross_section,undersizing);
	}else if(goal==1){ // mold bottom half
		difference(){
			translate([0,0,-tomm(minionizing_cross_section,units)]) union() {
				translate([
					-(tomm(outside_diameter,units)+mold_perimeter)/2,
					-(tomm(outside_diameter,units)+mold_perimeter)/2,
					(-cross_sectional_diameter/2)-(fn_cross_sectional_diameter(inside_diameter,outside_diameter,cross_sectional_diameter)/2+(mold_perimeter/2))
					]) 
					cube([tomm(outside_diameter,units)+mold_perimeter,tomm(outside_diameter,units)+mold_perimeter,fn_cross_sectional_diameter(inside_diameter,outside_diameter,cross_sectional_diameter)+(mold_perimeter/2)+tomm(minionizing_cross_section,units)]);
				// key
				translate([0,0,tomm(minionizing_cross_section,units)]) sphere ([mold_perimeter*4,mold_perimeter*4,mold_perimeter*4]);
			}
			create_o_ring(units,outside_diameter,cross_sectional_diameter,inside_diameter,minionizing_cross_section,undersizing);
		}
	}else{ // mold top half
		rotate([180,0,0]) difference(){ 
			union() {
				translate([
					-(tomm(outside_diameter,units)+mold_perimeter)/2,
					-(tomm(outside_diameter,units)+mold_perimeter)/2,
					(-cross_sectional_diameter/2)+(-fn_cross_sectional_diameter(inside_diameter,outside_diameter,cross_sectional_diameter)/2+(mold_perimeter/2))
					])
					//cylinder(d=tomm(outside_diameter,units)+mold_perimeter,$fs=6);
					cube([tomm(outside_diameter,units)+mold_perimeter,tomm(outside_diameter,units)+mold_perimeter,fn_cross_sectional_diameter(inside_diameter,outside_diameter,cross_sectional_diameter)+(mold_perimeter/2)]);
				// inlet riser
				translate([(fn_inside_diameter(inside_diameter,outside_diameter,cross_sectional_diameter)/2-((mold_hole_size+fn_cross_sectional_diameter(inside_diameter,outside_diameter,cross_sectional_diameter))/2))-(mold_hole_size/2)+(mold_perimeter/2),0,0]) cylinder(r=(mold_hole_size+mold_perimeter)/2,h=riser_height);
			}
			// key hole
			sphere ([mold_perimeter*4,mold_perimeter*4,mold_perimeter*4]);
			// o-ring
			create_o_ring(units,outside_diameter,cross_sectional_diameter,inside_diameter,0,undersizing);
			// inlet hole
			translate([(fn_inside_diameter(inside_diameter,outside_diameter,cross_sectional_diameter)/2-((mold_hole_size+fn_cross_sectional_diameter(inside_diameter,outside_diameter,cross_sectional_diameter))/2)),0,-50]) cylinder(r=mold_hole_size/2,h=100);
			translate([(fn_inside_diameter(inside_diameter,outside_diameter,cross_sectional_diameter)/2-((mold_hole_size+fn_cross_sectional_diameter(inside_diameter,outside_diameter,cross_sectional_diameter))/2)),0,-sprue_thickness]) cylinder(r=(mold_hole_size+fn_cross_sectional_diameter(inside_diameter,outside_diameter,cross_sectional_diameter))/2,h=sprue_thickness);
			// vent hole
			translate([-(fn_inside_diameter(inside_diameter,outside_diameter,cross_sectional_diameter)/2-((mold_hole_size+fn_cross_sectional_diameter(inside_diameter,outside_diameter,cross_sectional_diameter))/2)),0,-50]) cylinder(r=mold_hole_size/2,h=100);
			translate([-(fn_inside_diameter(inside_diameter,outside_diameter,cross_sectional_diameter)/2-((mold_hole_size+fn_cross_sectional_diameter(inside_diameter,outside_diameter,cross_sectional_diameter))/2)),0,-sprue_thickness]) cylinder(r=(mold_hole_size+fn_cross_sectional_diameter(inside_diameter,outside_diameter,cross_sectional_diameter))/2,h=sprue_thickness);
		}
	}
}

//---- The program
o_ringer(goal,units,outside_diameter,cross_sectional_diameter,inside_diameter,minionizing_cross_section,undersizing,mold_perimeter,mold_hole_size,riser_height,sprue_thickness);