// [FL_INDEX: keywords="openscad, 3d_parametric, Locking_key_for_Ultimaker_filament_feeder__aka__extruder, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Locking key for Ultimaker filament feeder (aka "extruder")

// Total width
handleWidth=20;
// Individual arm width
armWidth=6;
// Arm length
armLength=20;
// Arm smaller height (in the frame)
armHeight1=5.0;
// Arm outer height (near the handle)
armHeight2=7.5;

// Ultimaker Extruder/Feeder locking key
// jeremie.francois@gmail.com / MoonCactus on thingiverse / www.tridimake.com
// Rev B: compatible with the customizer for other geometries

handleDiameter= armHeight2;

tol=0.02+0;

armGap=16-armWidth*2;
$fa=1;
$fs=1;
module arm()
{
	translate([-(armWidth+armGap+armWidth)/2,0,0])
	difference()
	{
		hull()
		{
			cube([armWidth+armGap+armWidth,tol,armHeight1]);
			translate([0,armLength-tol,0])
				cube([armWidth+armGap+armWidth,tol,armHeight2]);
		}
		translate([armWidth,-tol,-tol])
			cube([armGap,armLength,armHeight2+0.01]);
	}
	hull()
	{
		for(s=[-1,+1]) scale([s,1,1])
		translate([-handleWidth/2, armLength, handleDiameter/2]) sphere(r=handleDiameter/2);
	}
}

arm();