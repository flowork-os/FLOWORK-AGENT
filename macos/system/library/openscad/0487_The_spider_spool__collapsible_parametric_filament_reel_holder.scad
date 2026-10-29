// [FL_INDEX: keywords="openscad, 3d_parametric, The_spider_spool__collapsible_parametric_filament_reel_holder, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: The spider spool (collapsible parametric filament reel holder)

tol=1*0.1;

/* [Main] */

// Which part to display (preview only for... previewing)
show="preview"; // [preview, hub, arm, attachment]
//show="hub";
//show="arm";
//show="attachment";
//show="hooks"; // only for UM with my hooks

// Number of arms
nb_arms=3; // [3, 4, 5, 6]

/* [Tuning (only visual)] */

// Approximative geomery of the filament roll
shown_roll_id= 200;
// Outer diameter
shown_roll_od= 320;
// Thickness
shown_roll_th= 40;

// Just for display, how opened are the arms
shown_arm_angle= 48; // [20:90]

/* [Main geometry] */

// Axis/rod diameter
tube_d=8;

// Arm: main axis to arm shoulder
hub_ear_len=6; // [0:200]
// Arm: shoulder to elbow junction
arm_hinge= 35; // [0:200]
// Arm: first arm segment after junction
arm_len= 65; // [0:200]
// Arm: outer arm segment
arm_hand_len= 45; // [0:200]
// Arm: angle of the outer arm segment
arm_hand_hangle= 35; // [0:90]

fp= 0*0.4; // freeplay on rotational junctions

/* [Advanced settings] */

// Axis/rod freeplay
tube_dd=0.1;

// Arm thickness
wall_th=4;           // [3:8]
// Arm section height
arm_h=10;            // [5:20]
// Hub height
hub_h= 15;           // [5:30]

/* [Rod holder] */

// Plate thickness
hook_th= 4;
// Distance from screw to screw
hook_sc2sc= 40;
// Diameter for the hook attachment screws
hook_screw_d= 3;
// Height
hook_height=20;
// Width
hook_width= 30;
// Nut diameter
hook_nut_d=14.38;
// Nut thickness
hook_nut_h=6.8;

// ========== computed values (do not modify)

hub_r= (tube_d+tube_dd)/2+wall_th;

// Computed position of the arm rotation axis (only to tune the display)
ear_start_x= (tube_d-tube_dd)/2+wall_th;
ear_start_z= -(hub_h-arm_h)/2;

// Relative distance to the rotational axis of the arms (for display only)
rot_x2= ear_start_x + hub_ear_len + cos(shown_arm_angle)*(arm_hinge + arm_h/2) + sin(shown_arm_angle)*(arm_h/2);
rot_z2= ear_start_z + -sin(shown_arm_angle)*(arm_hinge + arm_h/2) + cos(shown_arm_angle)*(arm_h/2);
%translate([rot_x2,0,rot_z2]) rotate([90,0,0]) cylinder(r=2,h=80,center=true);

hub_shown_distance= rot_z2*2;

if(show=="preview")
{
	%union()
	{
		// axis
		translate([0,0,rot_z2]) cylinder(r=(tube_d+tube_dd)/2-tol, h=-rot_z2*2 + 2*hub_h, center=true);
		// pseudo roll
		translate([0,0,hub_shown_distance/2])
			difference() { cylinder(r=shown_roll_od/2,h=shown_roll_th,center=true); cylinder(r=shown_roll_id/2,h=shown_roll_th+1,center=true); }
	}

	hub(witharms=true);
	color([1,0.5,0.5]) translate([0,0,hub_shown_distance]) rotate([180,0,0])
		hub(witharms=true);

//	translate([0,0,-arm_len/2-30])
	translate([0,0,rot_z2*2 - hub_h/2 - hook_height - 1])
	{
		color([0,1,0.5]) um_attachment();
		//color([1,0.5,1]) translate([0,-8,-8]) rotate([0,90,90])
		//	um_hooks(wall_th=6, height=44, um_hook_width=hook_width);
	}
}
else if(show=="hub")
{
	hub(); // you need 2
}
else if(show=="arm")
{
	rotate([180,0,0])
		arm(); // you need (2 x nb_arms)
}
else if(show=="attachment")
{
	um_attachment();
}
else if(show=="hooks")
{
	//rotate([0,-90,0]) um_hooks(wall_th=6, height=44, um_hook_width=hook_width);
}


module chain_hull()
{
	for(i=[0:$children-2])
		hull()
			for(j=[i,i+1])
				child(j);
}

module um_attachment()
{
	difference()
	{
		union()
		{
			difference()
			{
				hull()
					for(x=[-1,+1])
						translate([x*hook_sc2sc/2,0,0])
						{
							cylinder(r=hook_width/2, h=hook_th-2);
							translate([0,0,hook_th])
								gopro_torus(r=hook_width/2, rnd=2);
						}
				// M3 bolt holes
				for(x=[-1,+1])
							translate([x*hook_sc2sc/2,0,-tol])
								cylinder(r=hook_screw_d/2, h=10, $fs=1);
			}

			hull()
			{
				cylinder(r=(tube_d-tube_dd)/2+wall_th,h=hook_height);
				translate([0,0,3]) cube([30,wall_th,2],center=true);
			}
		}
		
		translate([0,0,-tol])
		{
			cylinder(r=(tube_d-tube_dd)/2 - 0.1,h=31);
			cylinder(r=hook_nut_d/2,$fn=6,h=hook_nut_h);
		}
	}
}

module ear(main_rot_angle)
{
	rotate([90,0,0])
		translate([ear_start_x, ear_start_z, 0])
	{
		difference()
		{
			union()
			{
				for(x=[-1,+1]) translate([0,0,x*wall_th])
				hull()
				{
					translate([-arm_h+1,0,0]) scale([0.1,1,1])
						gopro_rcyl(r=arm_h/2, h=wall_th,center=true, rnd=3);
					translate([hub_ear_len-arm_h+1,0,0]) scale([0.1,1,1])
						gopro_rcyl(r=arm_h/2, h=wall_th,center=true, rnd=3);
				}
				hull()
				{
					translate([hub_ear_len-arm_h+1,0,0]) scale([0.5,1,1])
						gopro_rcyl(r=arm_h/2, h=wall_th*4,center=true, rnd=3);
					translate([hub_ear_len+fp,0,0])
						gopro_rcyl(r=arm_h/2, h=wall_th*4,center=true, rnd=3);
				}
			}
			translate([hub_ear_len+fp,0,0])
			{
				cylinder(r=3/2, h=4*wall_th+1,center=true,$fs=1);
				cube([arm_h+fp*2, arm_h+fp*2+2*tol, wall_th*2+fp*2],center=true);
			}
		}
	}
}

module hub(witharms=false)
{
	difference()
	{
		union()
		{
			gopro_rcyl(r=hub_r, h=hub_h,center=true,rnd=3);
			
			for(r=[0:360/nb_arms:359])
				rotate([0,0,r])
				{
					ear(r);

					if(witharms)
						translate([(tube_d-tube_dd)/2+wall_th + hub_ear_len+fp, 0, -(hub_h-arm_h)/2])
							rotate([90,shown_arm_angle,0])
								arm(r);
				}
		}
		cylinder(r=(tube_d+tube_dd)/2, h=hub_h+2,center=true);
	}
}

module gopro_torus(r,rnd)
{
	translate([0,0,rnd/2])
		rotate_extrude(convexity= 10)
			translate([r-rnd/2, 0, 0])
				circle(r= rnd/2, $fs=0.2);
}

module gopro_rcyl(r,h, center=false, rnd=1)
{
	translate([0,0,center ? -h/2 : 0])
	hull() {
		translate([0,0,0]) gopro_torus(r=r, rnd=rnd);
		translate([0,0,h-rnd]) gopro_torus(r=r, rnd=rnd);
	}
}

module arm_section()
{
	gopro_rcyl(r=arm_h/2, h=wall_th-fp,center=true, rnd=2);
}

module arm(main_rot_angle)
{
  difference()
  {
    union()
    {
      cylinder(r=arm_h/2, h=wall_th*2-fp,center=true); // large shoulder
      translate([0,0,wall_th/2])
      {
	difference()
	{
	  union()
	  {
	    chain_hull()
	    {
	      arm_section();
	      translate([arm_hinge,0,0]) arm_section();
	      translate([arm_hinge + arm_h, arm_h,0]) arm_section();
	      translate([arm_len + arm_h, arm_h,0]) arm_section();
	    }
	    translate([arm_len + arm_h, arm_h, 0])
	      hull()
	      {
		arm_section();
		rotate([0,0,arm_hand_hangle])
		  translate([arm_hand_len,0,0]) arm_section();
	      }
	  }
	  translate([arm_hinge + arm_h/2, arm_h/2,0])
	    cylinder(r=3/2,h=wall_th+1,center=true,$fs=1); // hinge

	  // holes used to fix the filament end
	  translate([arm_len + arm_h - 6, arm_h,0])
	    cylinder(r=3.1/2,h=wall_th+1,center=true,$fs=1); // hinge
	  translate([arm_len + arm_h, arm_h, 0])
	      rotate([0,0,arm_hand_hangle])
		translate([arm_hand_len-3,0,0])
		  cylinder(r=3.1/2,h=wall_th+1,center=true,$fs=1); // hinge
	  
	}
      }
    }
    cylinder(r=3/2, h=wall_th*2+1,center=true,$fs=1); // attachment hole
    
  }
}