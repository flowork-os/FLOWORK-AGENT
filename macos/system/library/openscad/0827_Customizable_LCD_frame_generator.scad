// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_LCD_frame_generator, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable LCD frame generator

/*
Create a LCD frame for 3D printing
Create by Dave Borghuis / zeno4ever
Version : 1.1
Date : 10-02-2023
For sugestions email me at : zeno4ever@gmail.com
*/

//Size of LCD
lcd_horizontal = 62;
lcd_vertical = 18;

//border around the frame
lcd_frame = 4;

//border inside frame, set to 0 to disable
lcd_inner = 2;

//hight of the frame
frame_hight = 6;

//for barb thickness of used material
material_thickness = 1; 

wall_thickness = 2*1; //wall thickness * 1 to disable for thiniverse customise

//internal parameters
frame_horizontal = lcd_horizontal+lcd_frame;
frame_vertical = lcd_vertical+lcd_frame;
lcd_inner_thickness = 2*0.2; //2 layers



barb_size = 2*1; //with of barb (top)
barb_size_b = 0; //with of barb (bottom) barb_size/2;

//set resolution
$fs = 0.6*1; 

//make frame
module makeframe () {
	difference () {
		difference () {	//inner frame
			cube(size = [frame_vertical,frame_horizontal,frame_hight],center=true);
			translate([0,0,-lcd_inner_thickness]) cube(size = [lcd_vertical,lcd_horizontal,frame_hight],center=true);
            
        	translate([0,0,0]) cube(size = [lcd_vertical-lcd_inner,lcd_horizontal-lcd_inner,frame_hight],center=true);
        
            
            
		}	

		translate([0,0,-wall_thickness]) difference () {	//outer frame
			cube(size = [frame_vertical+wall_thickness,frame_horizontal+wall_thickness,frame_hight+wall_thickness],center=true);        
            
        translate([0,0,0]) 			cube(size = [lcd_vertical+wall_thickness,lcd_horizontal+wall_thickness,frame_hight+wall_thickness],center=true);
            
		}
	}
    
    //inner frame 
    if (false) {
        #translate([0,0,-1]) 			cube(size = [lcd_vertical+wall_thickness,lcd_horizontal+wall_thickness,frame_hight+wall_thickness],center=true);
    
    
    }


	//make barbs
	fz = -(frame_hight)/2;

	//side brad
	fx = frame_vertical/4;
	fy = (lcd_horizontal+wall_thickness)/2;

	//top/bottom brad
	fx2 = (lcd_vertical+wall_thickness)/2;
	fy2 = frame_horizontal/4;

	difference () {
		union () {
			for (factorx = [-1,1]) {
				for (factory = [-1,1]) {
					translate ([factorx*fx ,factory*fy,fz]) barb();
				}
			}

			for (factorx = [-1,1]) {
				for (factory = [-1,1]) {
					translate ([factorx*fx2 ,factory*fy2,fz]) barb();
				}
			}
		}
		cube(size = [lcd_vertical,lcd_horizontal,frame_hight],center=true);
	};
};


module barb() {
	cylinder(h = frame_hight-material_thickness-wall_thickness, r1 = barb_size_b, r2 = barb_size, center = false);
};


translate([0,0,frame_hight/2]) rotate ([0,180,0]) makeframe();