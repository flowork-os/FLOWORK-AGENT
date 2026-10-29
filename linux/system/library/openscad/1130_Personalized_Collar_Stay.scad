// [FL_INDEX: keywords="openscad, 3d_parametric, Personalized_Collar_Stay, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Personalized Collar Stay

/* variable description */
/* [General] */
// Choose to use Text or Images, then go to the Text or Image Options tab to further customize.
text_or_image = "Text"; //[Text,Image]
collar_stay_length = 50;
collar_stay_height = 10;
collar_stay_thickness = 1.8;
collar_stay_tip_length = 10; //[5:30]
pairs_of_stays = 5;
build_plate_selector = 2; //[0:Replicator 2,1: Replicator,2:Thingomatic]

/* [Text Options] */
font = "write/letters.dxf"; //["write/Letters.dxf":Basic,"write/orbitron.dxf":Futuristic,"write/BlackRose.dxf":Fancy]
text = "GEEK";
text_x_size = 7; //[1:20]
text_y_size = 6; //[1:10]
// Height of Text in mm (Use positive values for raised relief, use negative values for inset. To create complete cutouts of letters, set this value greater than the negative of the collar stay thickness)
text_height = -0.5;

/* [Image Options] */
// Load a 150x40px image. (Images will be automatically stretched to fit, don't worry too much about image size, the scaling options below will let you fine tune) Simple, high contrast images like logos work best.
image_file = "image-surface.dat"; // [image_surface:150x40]
image_x_size = 50; // [1:100]
image_y_size = 50; // [1:100]
// Height of Image in mm (Use positive numbers for raised relief, use negative numbers for inset)
image_height = .5;

/* [Advanced Options] */
//If mirrored, then half of the collar stays will point the other direction. If not mirrored, then all collar stays are identical.
mirror_stays = 1; //[0:No Mirror,1:Mirror]
// Positive values to increase spacing, negative values to decrease spacing.
gap_x = 2;
// Positive values to increase spacing, negative values to decrease spacing.
gap_y = 2;

/* [hidden] */
collar_stay_butt = collar_stay_height / 2;
collar_stay_body = collar_stay_length - collar_stay_butt - collar_stay_tip_length;

preview_tab = "General";
// preview[view:east, tilt:top]

use <utils/build_plate.scad>
use <write/Write.scad> 

if (preview_tab == "General" || preview_tab == "Advanced options")
{
	build_plate(build_plate_selector,build_plate_manual_x,build_plate_manual_y);

	rotate([0,0,90])
	{
		translate([-1*collar_stay_length + collar_stay_tip_length/2 + collar_stay_butt/2, -.5*(collar_stay_height+gap_y)*(pairs_of_stays) - (collar_stay_height+gap_y)*1.125,0])
		{
			for(y = [0:1])
			{
				translate([(2*collar_stay_length - collar_stay_tip_length - collar_stay_butt + gap_x - 2)*y,((collar_stay_height + gap_y)*(pairs_of_stays+2) + collar_stay_height*.5 - gap_y/2)*y, 0])
				{
					rotate(a=[0,0,180*y])
					{
						for(z = [1:pairs_of_stays]) 
						{
							translate( [0 , ((collar_stay_height+gap_y)*z), 0])
							{
								draw_edited_stay(y*mirror_stays);
							}
						}
					}
				}
			}
		}
	}
}

else if (preview_tab == "Text options" || preview_tab == "Image options")
{
	rotate([0,0,90])
	{
		draw_edited_stay();
	}	
}

module draw_edited_stay(y)
{
	if (text_or_image == "Image")
	{
		if (image_height >= 0)
		{
			union()
			{
				draw_stay();
				draw_image(y);
			}
		}
		else
		{
			difference()
			{
				draw_stay();
				draw_image(y);
			}
		}
	}
	else if (text_or_image == "Text")
	{
		if (text_height >= 0)
		{
			union()
			{
				draw_stay();
				draw_text(y);
			}
		}
		else
		{
			difference()
			{
				draw_stay();
				draw_text(y);
			}
		}
	}
}

module draw_stay()
{
	hull()
	{
		translate([collar_stay_length-collar_stay_tip_length-collar_stay_butt, collar_stay_height/2 , 0])
			cylinder (h=collar_stay_thickness, r=collar_stay_height/2, $fn=100);							// butt part
		translate(v=[0,collar_stay_height/2,0])
			cylinder(h=collar_stay_thickness, r=(collar_stay_height/2), $fn=100);							// angle part
		translate(v=[collar_stay_length-collar_stay_butt-1,(collar_stay_height/2),0])
			cylinder(h=collar_stay_thickness, r=1, $fn=40);											// tip part
	}
}

module draw_text(y)
{
	translate([(collar_stay_length-collar_stay_tip_length-collar_stay_butt)/2,collar_stay_height/2,collar_stay_thickness+(text_height/2) - text_height/100])
		rotate([0,0,180*y])
		scale([(text_x_size/10),(text_y_size/11),1])
			write(text, t=text_height, h=collar_stay_height, center=true, font=font);
}

module draw_image(y)
{
	translate([(collar_stay_length-collar_stay_tip_length-collar_stay_butt)/2,collar_stay_height/2,collar_stay_thickness+(image_height/2) - (image_height/2) - image_height/100])
		rotate([0,0,180*y])
		scale([((collar_stay_body)/150)*(image_x_size/50),(collar_stay_height/40)*(image_y_size/50),image_height]) 
			difference ()
			{	
				surface(file=image_file, center=true, convexity=5); 
					translate ([-100,-100,-2]) cube([200, 200, 2]);
			}
}