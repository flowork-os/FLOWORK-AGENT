// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_Oval_Keychain, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable Oval Keychain

include <write/Write.scad>
include <utils/build_plate.scad>

/* [Main] */

//(mm)
width=25;
//(mm)
length=50;
//(mm)
height=1.6;
//Height/Width of lip (mm)
lip=0.4;


/* [Text] */

text="Hello World";
text_size = 6;
text_font = "write/Letters.dxf";//["write/Letters.dxf":Basic,"write/orbitron.dxf":Futuristic,"write/BlackRose.dxf":Fancy]


/* [Ring] */

ring_radius=1.6;
ring_thickness=0.8;

/* [Build Plate] */

//for display only, doesn't contribute to final object
build_plate_selector = 0; //[0:Replicator 2,1: Replicator,2:Thingomatic,3:Manual]

//when Build Plate Selector is set to "manual" this controls the build plate x dimension
build_plate_manual_x = 100; //[100:400]

//when Build Plate Selector is set to "manual" this controls the build plate y dimension
build_plate_manual_y = 100; //[100:400]

/* [Hidden] */

kf_fn=25;



// preview[view:south east, tilt:top]

build_plate(build_plate_selector,build_plate_manual_x,build_plate_manual_y); 


module ovalKeyChain(plateWidth=width, plateLength=length, wall=lip,plateHeight=height, tabRadius=ring_radius, tabThickness=ring_thickness,fn=kf_fn)
{
	innerRadius = (plateWidth/2)-(wall/2);
	actualBase = plateHeight-wall;
	scale = (plateLength-wall)/(plateWidth-wall);

	difference()
	{
		union()
		{
			minkowski()
			{
				scale([scale,1,1])
				{
					cylinder(r=innerRadius, h=actualBase, $fn=fn);
				}
				translate([-wall/scale,-wall/scale,0])
				{
					cube(wall);
				}
			}

			translate([-plateLength/2,0,0])
				rotate_extrude(convexity = 10, $fn=fn)
					translate([tabRadius, 0, 0])
						square([tabThickness,tabThickness]);

		
		}
		union()
		{
			translate([0,0,actualBase])
			{
				scale([scale,1,1.5])
				{
					cylinder(r=innerRadius, h=actualBase,$fn=fn);
				}
			}

		}
	}


}

module renderText(txt=text, txtSize=text_size, txtFont=text_font, txtDepth=height)
{
	translate([0,0,txtDepth/2])
		write(txt,h=txtSize,t=txtDepth,font=txtFont,center=true);
}


ovalKeyChain();
renderText();

