// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_Easter_Artistic_Eggs, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable Easter Artistic Eggs

// Joe Stubbs
// February 24 2012
// http://www.thingiverse.com/thing:53816


use <utils/build_plate.scad>

$fn = 50*1;

//Select the style of egg you would like to create.  If your loops are not touching you will need to select an shell style to hold everything together
Egg_Style = 5; // [0:Plain,1:Single,2:Double,3:Triple, 4:Single Shell,5:Double Shell,6:Triple Shell]

//Width of the egg in mm.
Egg_Width = 60; //[30:200]

//Select the basic shape to apply to your vase design
Basic_Shapes = 50; //[50:Ovals,3:Triangles,4:Diamonds,6:Emeralds]

Line_Width = 2; //[1:1mm Very Thin,2:2mm Thin,3:3mm Normal,4:4mm Thick,5:5mm Thicker]

//Number of loops around your egg:
Loops = 9; // [1:40]

//How wide do you want each loop to be?
Loop_Width = 0.5; // [0.1:Very Narrow,0.2:Narrow,0.3:Medium,0.4:Wide,0.5:Very Wide]

//How much do you want each loop to overlap vertically. Note: This only applies to double or triple Egg Styles.
Loop_Overlap = 0.375; // [0.0:None,0.125:Very Little,0.25:Half,0.375:Most,0.5:Full]

//This setting allows you to offset the loops for some interesting effects
Loop_Angle_Offset = 0.25; // [0:In line,0.5:Staggered,0.25:Split Staggered]

//This setting only applies to triple Egg Styles. It sets the ratio between the middle loop and the other two loops.
Middle_Loop_Ratio =  3; //[0.1:10%,0.2:20%,0.3:30%,0.4:40%,0.5:50%,0.6:60%,0.7:70%,0.8:80%,0.9:90%,1.0:100%,1.1:110%,1.2:120%,1.3:130%,1.4:140%,1.5:150%,1.6:160%,1.7:170%,1.8:180%,1.9:190%,2.0:200%]

//You can create some interesting effects with this setting.  In the triple Egg Styles the top and bottom loops skip, in the double Egg only the top skips.
Skip_Loops = 0; //[1:Yes,0:No]

//Applies to shell Egg Styles only, fill the shell of your egg to create a unique look.  Set the value to 100% if you want the egg shell to be complete all the way to the top.
Shell_Perentage = 0.6; //[0.2:20%,0.3:30%,0.4:40%,0.5:50%,0.6:60%,0.7:70%,0.8:80%,0.9:90%,1.0:100%]

//Applies to shell Egg Styles with less than 100% shell.  You can adjust the angle of the partial shell.  This can create some interesting loops especially if you tilt the shell beyond 90 degrees.
Shell_Angle = 30; //[0:0 degrees,10:10 degrees,20:20 degrees,30:30 degrees,45:45 degrees,60:60 degrees,70:70 degrees,80:80 degrees,90:90 degrees,120:120 degrees,135:135 degrees,180:180 degrees]




//for display only, doesn't contribute to final object
build_plate_selector = 0; //[0:Replicator 2,1: Replicator,2:Thingomatic,3:Manual]

//when Build Plate Selector is set to "manual" this controls the build plate x dimension
build_plate_manual_x = 100; //[100:400]

//when Build Plate Selector is set to "manual" this controls the build plate y dimension
build_plate_manual_y = 100; //[100:400]

build_plate(build_plate_selector,build_plate_manual_x,build_plate_manual_y);






sphere_outside_d = Egg_Width;
sphere_outside_r = sphere_outside_d/2;

sphere_wall = Line_Width;

sphere_inside_d = sphere_outside_d-sphere_wall*2;
sphere_inside_r = sphere_inside_d/2;

sphere_middle_d = (sphere_outside_d+sphere_inside_d)/2;
sphere_middle_r = sphere_middle_d/2;



sphere_top_hole_d = sphere_outside_d*0.05;
sphere_top_hole_r = sphere_top_hole_d/2;
sphere_top_z = trig_b_for_a_c(sphere_top_hole_r,sphere_outside_r); // use pythagorus to determine the location of the top ring

sphere_top_z_mid = sphere_top_z-sphere_wall/2;





sphere_base_d = sphere_outside_d*0.05;
sphere_base_r = sphere_base_d/2;
sphere_base_z = -trig_b_for_a_c(sphere_base_r,sphere_outside_r); // use pythagorus to determine the location of thebase ring

sphere_base_z_mid = sphere_base_z+sphere_wall/2;


holy_vase_count = Loops;
holy_vase_hole_ratio = Loop_Width;
holy_vase_overlap_ratio = Loop_Overlap;
holy_vase_spin_offset_ratio = Loop_Angle_Offset;
holy_vase_skip_loops = Skip_Loops;



holy_vase_triple_middle_hole_ratio = Middle_Loop_Ratio ;


scale_z_top = 1.5*1;
scale_z_bottom = 1.1*1;

style= Egg_Style;
style_line = 1*1;


emboss_ratio = Shell_Perentage;
emboss_tilt = Shell_Angle;

holy_fn = Basic_Shapes ;

fudge = 0.05*1;



create_egg();



//create_vase();



module create_egg() {

	move_up_z = (sphere_outside_d/2)*scale_z_bottom;
	translate([0,0,move_up_z]) {
		scale([1,1,scale_z_top]) {
			intersection() {
				union() {	
					create_the_egg();
					if (style==4||style==5||style==6)
						basic_sphere_emboss ();
				}
				translate([0,0,(sphere_outside_d/2)/2])
					cylinder (r=sphere_outside_r+fudge,h=(sphere_outside_d/2+fudge),center=true);
			}
				
		}

	
		scale([1,1,scale_z_bottom]){
			intersection() {
				union() {
					create_the_egg();
					if (style==4||style==5||style==6)
						basic_sphere_emboss ();
				}
				translate([0,0,-(sphere_outside_d/2)/2])
					cylinder (r=sphere_outside_r+fudge,h=sphere_outside_d/2+fudge,center=true);
			}
		
		}
	}
}

module create_the_egg() {
	if (style==0)
		create_sphere_egg();
	if (style==1||style==4)
		create_single_holy_egg();
	if (style==2||style==5)
	 	create_double_holy_egg();
	if (style==3||style==6)
	 	 create_tripple_holy_egg();


}



module create_tripple_holy_egg () {  


	intersection() {
		basic_sphere ();
		union() {
			for (i=[1:holy_vase_count]) {
				if (holy_vase_skip_loops==0 || round ((i+1)/2)*2 == i+1) 
					tripple_top_holy_sphere (i,holy_vase_count);
			}
			for (i=[1:holy_vase_count]) {
				//if (holy_vase_skip_loops==0 || round ((i)/2)*2 == i) 
					tripple_middle_holy_sphere (i,holy_vase_count);
			}
			for (i=[1:holy_vase_count]) {
				if (holy_vase_skip_loops==0 || round ((i+1)/2)*2 == i+1) 
					tripple_bottom_holy_sphere (i,holy_vase_count);
			}
		}

	}     
}



module tripple_top_holy_sphere (x,of) {



	delta_y = abs(sphere_top_z-sphere_base_z); // distance between top and bottom
	middle_hole_y = delta_y/3*holy_vase_triple_middle_hole_ratio/2/2;
	middle_hole_y_with_top_overlap = middle_hole_y + (sphere_top_z-middle_hole_y)*holy_vase_overlap_ratio;
	middle_hole_y_with_bottom_overlap = -middle_hole_y + (sphere_base_z+middle_hole_y)*holy_vase_overlap_ratio;

	top_hole_y_with_overlap = middle_hole_y - (middle_hole_y*2)*holy_vase_overlap_ratio;
	bottom_hole_y_with_overlap = -middle_hole_y + (middle_hole_y*2)*holy_vase_overlap_ratio;


	top_x = sphere_top_hole_r;
	top_y = sphere_top_z;

	bottom_y = top_hole_y_with_overlap;
	bottom_x = trig_b_for_a_c(bottom_y,sphere_outside_r);
	
	basic_holy_sphere (top_x,top_y,bottom_x,bottom_y,x,of,0);



}


module tripple_bottom_holy_sphere (x,of) {

	delta_y = abs(sphere_top_z-sphere_base_z); // distance between top and bottom
	middle_hole_y = delta_y/3*holy_vase_triple_middle_hole_ratio/2/2;
	
	middle_hole_y_with_top_overlap = middle_hole_y + (sphere_top_z-middle_hole_y)*holy_vase_overlap_ratio;
	middle_hole_y_with_bottom_overlap = -middle_hole_y + (sphere_base_z+middle_hole_y)*holy_vase_overlap_ratio;

	top_hole_y_with_overlap = middle_hole_y - (middle_hole_y*2)*holy_vase_overlap_ratio;
	bottom_hole_y_with_overlap = -middle_hole_y + (middle_hole_y*2)*holy_vase_overlap_ratio;


	top_y = bottom_hole_y_with_overlap;
	top_x = trig_b_for_a_c(top_y,sphere_outside_r);

	bottom_x =sphere_base_r;
	bottom_y = sphere_base_z;

	
	if (holy_vase_spin_offset_ratio==0.25) {
		basic_holy_sphere (top_x,top_y,bottom_x,bottom_y,x,of,0.5);
	} else {
		basic_holy_sphere (top_x,top_y,bottom_x,bottom_y,x,of,0);
	}

}





module tripple_middle_holy_sphere (x,of) {

	delta_y = abs(sphere_top_z-sphere_base_z); // distance between top and bottom
	middle_hole_y = delta_y/3*holy_vase_triple_middle_hole_ratio/2/2;
	middle_hole_y_with_top_overlap = middle_hole_y + (sphere_top_z-middle_hole_y)*holy_vase_overlap_ratio;
	middle_hole_y_with_bottom_overlap = -middle_hole_y + (sphere_base_z+middle_hole_y)*holy_vase_overlap_ratio;

	top_hole_y_with_overlap = middle_hole_y - (middle_hole_y*2)*holy_vase_overlap_ratio;
	bottom_hole_y_with_overlap = -middle_hole_y + (middle_hole_y*2)*holy_vase_overlap_ratio;


	top_y = middle_hole_y_with_top_overlap;
	top_x = trig_b_for_a_c(top_y,sphere_outside_r);

	bottom_y = middle_hole_y_with_bottom_overlap;
	bottom_x = trig_b_for_a_c(bottom_y,sphere_outside_r);

	
	basic_holy_sphere (top_x,top_y,bottom_x,bottom_y,x,of,holy_vase_spin_offset_ratio);

}



module create_double_holy_egg () {  

	intersection() {
		basic_sphere ();
		union() {
			for (i=[1:holy_vase_count]) {
				if (holy_vase_skip_loops==0 || round ((i+1)/2)*2 == i+1) 
					double_top_holy_sphere (i,holy_vase_count,0);
			}
			for (i=[1:holy_vase_count]) {
				double_bottom_holy_sphere (i,holy_vase_count);
			}
		}

	}     

}                                                                          






module double_top_holy_sphere (x,of) {


	top_x = sphere_top_hole_r;
	top_y = sphere_top_z;

	bottom_y = sphere_base_z*holy_vase_overlap_ratio;
	bottom_x = trig_b_for_a_c(bottom_y,sphere_outside_r);
	
	basic_holy_sphere (top_x,top_y,bottom_x,bottom_y,x,of,0);

}


module double_bottom_holy_sphere (x,of) {


	top_y = sphere_top_z*holy_vase_overlap_ratio;
	top_x = trig_b_for_a_c(top_y,sphere_outside_r);


	bottom_x =sphere_base_r;
	bottom_y = sphere_base_z;


	basic_holy_sphere (top_x,top_y,bottom_x,bottom_y,x,of,holy_vase_spin_offset_ratio);
	
}





module angled_out_holy_sphere (top_x,top_y,bottom_x,bottom_y,x,of,spin_offset_ratio=0) {


	holy_wall = sphere_wall;
	holy_outside_d = distance (top_x,top_y,bottom_x,bottom_y);
	holy_outside_r = holy_outside_d/2;

	holy_inside_d=holy_outside_d-holy_wall*2;
	holy_inside_r=holy_inside_d/2;

	hole_outside_h = sphere_outside_r+fudge;

	tilt_angle = angle_to_midpoint (top_x,top_y,bottom_x,bottom_y);
	
	spin_angle = 360/of;	

	holy_inside_ratio = ((holy_outside_r*holy_vase_hole_ratio)-(sphere_wall/2))/holy_inside_r;



	rotate(spin_angle*(x-1)+(spin_angle*spin_offset_ratio),[0,0,1])
		if (top_y+bottom_y>=0) {
			rotate(tilt_angle,[0,1,0])

				translate([0,0,hole_outside_h/2])
					difference() {
						scale([1,holy_vase_hole_ratio,1]) 
							cylinder(r=holy_outside_r,h=hole_outside_h ,center=true,$fn=holy_fn); 
						scale([1,holy_inside_ratio,1]) 
							cylinder(r=holy_inside_r,h=hole_outside_h+fudge,center=true,$fn=holy_fn); 

					}
		} else {
			rotate(tilt_angle+180,[0,1,0])

				translate([0,0,hole_outside_h/2])
					difference() {
						scale([1,holy_vase_hole_ratio,1]) 
							cylinder(r=holy_outside_r,h=hole_outside_h ,center=true,$fn=holy_fn); 
						scale([1,holy_inside_ratio,1]) 
							cylinder(r=holy_inside_r,h=hole_outside_h+fudge,center=true,$fn=holy_fn); 

					}
		}


}










module create_sphere_egg () {
	basic_sphere ();

}


  

module basic_sphere () {
	difference() {
   		sphere(r = sphere_outside_r);
		sphere(r = sphere_inside_r);
	}
}

module basic_sphere_emboss () {



	difference() {
   		sphere(r = sphere_middle_r);
		sphere(r = sphere_inside_r-2);

		
		if (emboss_ratio < 1) 
			rotate(emboss_tilt,[0,1,0])
				translate([0,0,sphere_outside_r-(sphere_outside_d*(1-emboss_ratio))/2])
					cube([sphere_outside_d+fudge,sphere_outside_d+fudge,sphere_outside_d*(1-emboss_ratio)+fudge],center=true);


	}

}


	








           


module basic_holy_sphere (top_x,top_y,bottom_x,bottom_y,x,of,spin_offset_ratio=0) {
	if(style_line==1)
		angled_out_holy_sphere (top_x,top_y,bottom_x,bottom_y,x,of,spin_offset_ratio);
	
	if(style_line==2)
		angled_in_holy_sphere (top_x,top_y,bottom_x,bottom_y,x,of,spin_offset_ratio);
}




module single_holy_sphere (x,of) {

	top_x = sphere_top_hole_r;
	top_y = sphere_top_z;
	bottom_x =sphere_base_r;
	bottom_y = sphere_base_z;

	basic_holy_sphere (top_x,top_y,bottom_x,bottom_y,x,of,0);

}



module create_single_holy_egg () {  

	intersection() {
		basic_sphere ();
		union() {
			for (i=[1:holy_vase_count]) {
				single_holy_sphere (i,holy_vase_count);


			}
		}

	}    


 

}                                                                          




function trig_b_for_a_c(a,c) = sqrt((c*c)-(a*a));
function distance(x1,y1,x2,y2) = sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2));
function angle_to_midpoint(x1,y1,x2,y2) = atan(((x1+x2)/2)/((y1+y2)/2)); 