// [FL_INDEX: keywords="openscad, 3d_parametric, Parametric_Device_Mount, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Parametric Device Mount

/* [Device] */
device_thickness = 11.3;	
device_width = 72.6;	

/* [Clip] */
//how thick the material should be; too thick and it won't bend, too thin and it could be too loose or worse break
clip_thickness = 3;
//the width/height of the clip			
clip_width = 15;
//the length of the tabs that reach across the face of the device
clip_grip_length = 5;
//adds x space between all surfaces that contact device
gripping_tolerance = 0;

/* [Screw Attachments] */
//how deep the screw attachment is; note, screws can't go all the way through the clip; this prevents it from pressing against the device
screw_attachment_thickness = 6;
//increases the width of material surrounding where the screw will screw in
screw_width = 15;	
//adds a spot to attach a screw on the back center of the clip	
back_screw = "TRUE"; // [TRUE,FALSE]
//chooses where to place the back screw
back_screw_location = "CENTER"; // [TOP,CENTER,BOTTOM]
//adds a spot to attach a screw on the bottom of the clip
bottom_screw = "TRUE"; // [TRUE,FALSE]

/* [Screw Specifications] */
// specifies whether the screw is millimeters or inches; value of 1 for millimeters, value of 25.4 for inches
conversion = 25.4; // [1,25.4]
// the major diameter of the screw
diameter_major = 0.25;
// the pitch of the screw attachment
pitch = 0.05;
// integer multiplies the smoothness of the screw; suggested smoothness no greater than 5
Smoothness = 4;

/* [Hidden] */
arbitrary_device = [11.3,72.6,131.8];
Diameter_major = diameter_major*conversion;
Pitch = pitch*conversion;
Height = screw_attachment_thickness;
pi = 3.14159265359;
Circumference_major = Diameter_major*pi;
d27 = Pitch/8;
d28 = Pitch-d27;
d29 = 1.1*(Pitch-d27)/2;
number_of_bits = 8*Smoothness;
bit_thickness = 2.65/Smoothness;
$fn = 30;

A = [d28*cos(30),d28/2];
B = [d28*cos(30),d29];
C = [d28,d29];
D = [d28,-d29];
E = [d28*cos(30),-d29];
F = [d28*cos(30),-d28/2];
G = [d27*cos(30),-d27/2];
H = [d27*cos(30),d27/2];

module bit(Diameter_major,Pitch,Height,bit_thickness){
	translate([Diameter_major/2-d28*cos(30),bit_thickness/2,-d28/2+(d28+d27)*0]){
		rotate([90,0,0]){
			linear_extrude(height = bit_thickness)polygon(
				points = [A,B,C,D,E,F,G,H],
				paths = [[0,1,4,5,6,7]]
			);
		}
	}
}

module external_screw(Diameter_major,Pitch,Height,Smoothness){
	difference(){
		cylinder(r=Diameter_major/2-0.01,h=Height);
		for(j=[0:abs(Height)+1]){
			translate([0,0,Pitch*j]){
				rotate([0,0,j]){
					for(i=[0:(number_of_bits-1)]){
						translate([0,0,(1/number_of_bits)*Pitch*i]){
							rotate([0,0,(360/number_of_bits)*i]){
								bit(Diameter_major,Pitch,Height,bit_thickness);
							}
						}
					}
				}
			}
		}
	}
}

module screw_attachment(screw_width){
	difference(){
		translate([-screw_width/2,-clip_width/2,0]){
			cube([screw_width,clip_width,screw_attachment_thickness]);
		}
		translate([0,0,-0.1]){
			external_screw(Diameter_major,Pitch,Height+0.2,Smoothness);
		}
	}
}

module clip (){
	translate([0,clip_thickness/2,clip_width/2]){
		cube([device_width+gripping_tolerance*2,clip_thickness,clip_width],center=true);
	}
	translate([gripping_tolerance,0,0]){
		translate([(device_width)/2+clip_thickness/2,device_thickness/2+clip_thickness/2+gripping_tolerance,clip_width/2]){
			cube([clip_thickness,device_thickness+clip_thickness+gripping_tolerance*2,clip_width],center=true);
		}
		difference(){
			hull(){
				difference(){
					translate([device_width/2+clip_thickness,device_thickness+clip_thickness+gripping_tolerance*2,clip_width/2]){
						rotate([-90,0,0]){
							cylinder(r=clip_width/2,h=clip_thickness,$fn=30);
						}
					}
					translate([(device_width+gripping_tolerance)/2-clip_thickness*4/2,device_thickness/2+clip_thickness/2,clip_width/2]){
						cube([clip_thickness*4,device_thickness*5,clip_width*2],center=true);
					}
				}
				translate([device_width/2+clip_thickness/2-clip_grip_length,device_thickness+clip_thickness/2*3+gripping_tolerance*2,clip_width/2]){
					cube([clip_thickness,clip_thickness,clip_width],center=true);
				}
			}
			if(device_thickness < 5.2){
				translate([device_width/2+clip_thickness+gripping_tolerance,4,clip_width/2]){
					rotate([90,0,90]){
						external_screw(Diameter_major,Pitch,Height,Smoothness);
					}
				}
			}
		}
	}
	mirror(){
		translate([gripping_tolerance,0,0]){
			translate([(device_width)/2+clip_thickness/2,device_thickness/2+clip_thickness/2+gripping_tolerance,clip_width/2]){
				cube([clip_thickness,device_thickness+clip_thickness+gripping_tolerance*2,clip_width],center=true);
			}
			hull(){
				difference(){
					translate([device_width/2+clip_thickness,device_thickness+clip_thickness+gripping_tolerance*2,clip_width/2]){
						rotate([-90,0,0]){
							cylinder(r=clip_width/2,h=clip_thickness,$fn=30);
						}
					}
					translate([(device_width+gripping_tolerance)/2-clip_thickness*4/2,device_thickness/2+clip_thickness/2,clip_width/2]){
						cube([clip_thickness*4,device_thickness*5,clip_width*2],center=true);
					}
				}
				translate([device_width/2+clip_thickness/2-clip_grip_length,device_thickness+clip_thickness/2*3+gripping_tolerance*2,clip_width/2]){
					cube([clip_thickness,clip_thickness,clip_width],center=true);
				}
			}
		}
	}
	if(back_screw == "TRUE"){
		if(back_screw_location == "TOP"){
			translate([-device_width/2+screw_width/2-clip_thickness,0,clip_width/2]){
				rotate([90,0,0]){
					screw_attachment(screw_width);
				}
			}
		}
		if(back_screw_location == "CENTER"){
			translate([0,0,clip_width/2]){
				rotate([90,0,0]){
					screw_attachment(screw_width);
				}
			}
		}
		if(back_screw_location == "BOTTOM"){
			translate([device_width/2+clip_thickness-screw_width/2,0,clip_width/2]){
				rotate([90,0,0]){
					screw_attachment(screw_width);
				}
			}
		}
	}
	if(bottom_screw == "TRUE"){
		translate([device_width/2+clip_thickness+gripping_tolerance,(device_thickness+clip_thickness)/2,clip_width/2]){
			rotate([90,0,90]){
				screw_attachment(device_thickness+clip_thickness);
			}
		}
	}
}

module device (){
	translate([0,clip_thickness+arbitrary_device[0]/2,clip_width/2]){
		rotate([0,0,90]){
			cube(arbitrary_device,center=true);
		}
	}
}

//#translate([0,gripping_tolerance,0]){
//	device();							//used for visualizing how device fits in the grip with and without tolerances
//}

clip();