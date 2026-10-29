// [FL_INDEX: keywords="openscad, 3d_parametric, Custom_OptiTrack_Markers, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Custom OptiTrack Markers

//	Custom OptiTrack Marker Generator
// (c) James Walsh - james.walsh@setoreaustralia.com
// Original concept and prototype by Bruce Thomas (http://www.unisanet.unisa.edu.au/Staff/Homepage.asp?Name=Bruce.Thomas)

//CUSTOMIZER VARIABLES

//	Stand Width (X) (mm)
x_measurement = 10;

//	Stand Width (Y) (mm)
y_measurement = 10;

//	Stand Height (mm)
z_measurement = 10;

//	Marker Diameter (mm)
diameter = 10;	//	[5:40]

//	Number of Markers
marker_count = 5;	//	[1:5]

//	Max Marker Distance from Center
max_length = 7;	//	[5:15]

//Marker ID (Random Seed to Generate Marker)
seed = 150; // [0 : 300]

//CUSTOMIZER VARIABLES END

//core stand
translate([0,0,z_measurement/2]) cube([x_measurement, y_measurement, z_measurement], center=true);

//random marker offsets
rotX = rands(0, 180, marker_count, seed);
rotY = rands(0, 180, marker_count, seed);
rotZ = rands(0, 360, marker_count, seed);
lengthR = rands(diameter * 2, max(diameter * 5, max_length), marker_count, seed);

//draw the markers
for (i = [0 : marker_count])
{
	markerOnAStick(rotX[i] - 90, rotY[i] + 90, rotZ[i], lengthR[i], diameter);
}

module markerOnAStick(rotX, rotY, rotZ, length, diameter)
{
	rotate(rotX, [1, 0, 0])
	{
		rotate(rotY, [0, 1, 0])
		{
			rotate(0 , [0, 0, 1])
			{
				cylinder(length, diameter / 4);
				translate([0,0,length]) 
				{
					sphere(diameter / 2);
				}
			}
		}
	}
}