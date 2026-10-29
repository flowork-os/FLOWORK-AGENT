// [FL_INDEX: keywords="openscad, 3d_parametric, Filament_Odometer__v2, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Filament Odometer (v2)

include <write/Write.scad>
//Select what to print
PrintMode=0; //[1:Display Assembled,0:Single Print Bed]
//Select Wheel Diameter
WheelDia=35;
//Select Wheel Overlap
Over1=1.5;
//Shaft Diameter
Shaft=2.1;
//Number of faces on Wheel
Format=10;
//Default cyliner resolutions
res1=25;
res2=50;
res3=100;
//Pi constant
Pi=3.141592653589793238462643382795;
//Calculate Wheel Width
WheelWidth=(Pi*WheelDia)/Format;
//Total Number of Digits
Digits=3;
//Digit Seperation
Seperation=5;
//Clearance on moving part
Clearance1=1.5;
//Digit Spacing
Spacing=Clearance1*4+WheelWidth+Over1*4+Seperation;
//Units of measure
Units=10; // [10:cm,25.4:in]
//Width of Side Gears
SideWidth=Over1*2;
//Width of Drive Gears
DriveWidth=Spacing-(WheelWidth+Over1*2)-Clearance1;
//Spacing between gears and wheels
ShaftSpacing=WheelDia-(WheelDia/10);
//Excess clearance on body sides
Clearance2=4;
//Length of Body
BodyLength=(Clearance1*4+WheelWidth+Over1*4+Seperation)*Digits+Spacing;
//number of teeth on Feed Wheel
TeethFeed=round(((Pi*WheelDia)/Units)-.5);
//Feed Wheel Dia
FeedDia=(Units*TeethFeed)/Pi;
//Thickness of filament of rope
Filament=1.75;
//tension on filament (How close rollers are together)
Tension=0.25;
//Calculation of filament spacing
FilamentSpacing=Filament-Tension;
//Width of Body
BodyWidth=WheelDia+ShaftSpacing+Clearance2*2;
//Width of drive wheel system



module NumberedWheels(){
	difference(){
		union(){
			cylinder(r=WheelDia/2,h=Over1,$fn=res3);
			translate([0,0,WheelWidth+Over1]) cylinder(r=WheelDia/2,h=Over1,$fn=res3);
			translate([0,0,Over1]) cylinder(r=WheelDia/2,h=WheelWidth,$fn=Format);
		}
		translate([0,0,WheelWidth/2]) cube([WheelDia/3,WheelDia/3,WheelWidth*2],center=true);
		rotate([0,0,72])if (Format==10){
			rotate([0,0,0]) rotate([0,90,0]) translate([-WheelWidth/2-Over1,-WheelDia/2+.5,0]) writecube("0",h=WheelWidth/2);
			rotate([0,0,36*1]) rotate([0,90,0]) translate([-WheelWidth/2-Over1,-WheelDia/2+.5,0]) writecube("1",[0,0,0],[0,0,0],h=WheelWidth/2);
			rotate([0,0,36*2]) rotate([0,90,0]) translate([-WheelWidth/2-Over1,-WheelDia/2+.5,0]) writecube("2",[0,0,0],[0,0,0],h=WheelWidth/2);
			rotate([0,0,36*3]) rotate([0,90,0]) translate([-WheelWidth/2-Over1,-WheelDia/2+.5,0]) writecube("3",[0,0,0],[0,0,0],h=WheelWidth/2);
			rotate([0,0,36*4]) rotate([0,90,0]) translate([-WheelWidth/2-Over1,-WheelDia/2+.5,0]) writecube("4",[0,0,0],[0,0,0],h=WheelWidth/2);
			rotate([0,0,36*5]) rotate([0,90,0]) translate([-WheelWidth/2-Over1,-WheelDia/2+.5,0]) writecube("5",[0,0,0],[0,0,0],h=WheelWidth/2);
			rotate([0,0,36*6]) rotate([0,90,0]) translate([-WheelWidth/2-Over1,-WheelDia/2+.5,0]) writecube("6",[0,0,0],[0,0,0],h=WheelWidth/2);
			rotate([0,0,36*7]) rotate([0,90,0]) translate([-WheelWidth/2-Over1,-WheelDia/2+.5,0]) writecube("7",[0,0,0],[0,0,0],h=WheelWidth/2);
			rotate([0,0,36*8]) rotate([0,90,0]) translate([-WheelWidth/2-Over1,-WheelDia/2+.5,0]) writecube("8",[0,0,0],[0,0,0],h=WheelWidth/2);
			rotate([0,0,36*9]) rotate([0,90,0]) translate([-WheelWidth/2-Over1,-WheelDia/2+.5,0]) writecube("9",[0,0,0],[0,0,0],h=WheelWidth/2);
		}
	}
}
module SideGear(n){
	difference(){
		union(){
			rotate([0,0,108]) for (i=[1:n]){
				rotate([0,0,(360/n)*(i)]) translate([WheelDia/2-WheelDia/6,0,0]) intersection(){
					//cylinder(r=WheelWidth/2,h=2,$fn=res2);
					rotate([0,0,15]) cube([WheelDia/3,WheelDia/6,SideWidth],center=true);
					rotate([0,0,-15]) cube([WheelDia/3,WheelDia/6,SideWidth],center=true);
				}
			}
			translate([0,0,-Over1]) cylinder(r=WheelDia/3,h=SideWidth,$fn=res1);
			translate([0,0,-Over1*2])cube([WheelDia/3-.1,WheelDia/3-.1,Over1*3],center=true);
		}
		cylinder(r=Shaft,h=WheelWidth*2,center=true,$fn=res2);
	}

}
module DriveWheel(w){
	translate([0,0,w/2]) difference(){
		union(){
			for (i=[1:10]){
				rotate([0,0,36*i]) translate([WheelDia/2-WheelDia/6,0,0]) intersection(){
					rotate([0,0,15]) cube([WheelDia/3,WheelDia/6,w],center=true);
					rotate([0,0,-15]) cube([WheelDia/3,WheelDia/6,w],center=true);
				}
			}
			translate([0,0,-w/2]) cylinder(r=WheelDia/3,h=w,$fn=res1);
		}
		cylinder(r=Shaft,h=w*2,center=true,$fn=res2);
	}
}
module Odometer_Base(){
	difference(){
		translate([-WheelDia/2-Clearance2,-WheelDia/2-Clearance2,-Spacing-DriveWidth-Clearance1]) cube([WheelDia/2+Clearance2+Shaft*2,BodyWidth,BodyLength+DriveWidth]);
		for (i=[1:Digits]){
			translate([0,0,(Spacing)*(i-1)-Over1*2-Clearance1]) cylinder(r=(WheelDia/2)+Clearance1,h=WheelWidth+Over1*6+Clearance1*2,$fn=res2);
			translate([0,-(WheelDia/2)-Clearance1,(Spacing)*(i-1)-Over1*2-Clearance1]) cube([((WheelDia/2)+Clearance1)*2,((WheelDia/2)+Clearance1)*2,WheelWidth+Over1*6+Clearance1*2]);
			translate([0,ShaftSpacing,(-Spacing+WheelWidth+Over1*2-Clearance1/2)+(Spacing)*(i-1)]) cylinder(r=(WheelDia/2)+Clearance1,h=DriveWidth+Clearance1*2,$fn=res2);
			translate([0,ShaftSpacing-(WheelDia/2)-Clearance1,(-Spacing+WheelWidth+Over1*2-Clearance1/2)+(Spacing)*(i-1)]) cube([((WheelDia/2)+Clearance1)*2,((WheelDia/2)+Clearance1)*2,Spacing-(WheelWidth+Over1*2)+Clearance1]);
			translate([WheelDia/4+Shaft,0,Spacing*(i-1)-Over1*2-Clearance1*3]) cube([WheelDia/2,15,Clearance1], center=true);
		}
		rotate([0,180,0]) translate([0,0,DriveWidth-Clearance1]) cylinder (r=(WheelDia/2)+Clearance1,h=WheelWidth+DriveWidth+Clearance1*3,$fn=res3);
		rotate([0,0,0]) translate([0,ShaftSpacing,-Over1-WheelWidth-DriveWidth-5-Clearance1]) cylinder (r=ShaftSpacing-FeedDia/2-FilamentSpacing+Clearance1,h=DriveWidth+Clearance1,$fn=res3);
		rotate([0,90,0]) translate([25,DriveWidth+FilamentSpacing+(Filament*1.5),0]) cylinder(r=Filament+Clearance1,h=100,center=true,$fn=res3);
		translate([0,0,BodyWidth/2]) cylinder(r=Shaft,h=BodyWidth*3,$fn=res3,center=true);
		translate([0,ShaftSpacing,BodyWidth/2]) cylinder(r=Shaft,h=BodyWidth*3,$fn=res3,center=true);
	}
}
module FeedDriveWheel(){
	difference(){
		cylinder(r=FeedDia/2,h=WheelWidth+DriveWidth,$fn=res3);
		translate([0,0,WheelWidth]) cube([WheelDia/3,WheelDia/3,WheelWidth],center=true);
		cylinder(r=Shaft,h=WheelWidth*2,center=true,$fn=res2);
	}
}
module DriveWheelIdle(){
	difference(){
		cylinder(r=ShaftSpacing-FeedDia/2-FilamentSpacing,h=WheelWidth,$fn=res3);
		cylinder(r=Shaft,h=WheelWidth*3,center=true,$fn=res2);
	}
}
module Full_Assembly(){
	module Assembled_Numbered_Wheels(){
		NumberedWheels();
		color("Blue") rotate([180,0,0]) translate([0,0,Over1+.1]) SideGear(Format);
		color("Blue") rotate([0,0,0]) translate([0,0,Over1*3+WheelWidth+.1]) SideGear(1);
		color("green") rotate([0,0,-90]) translate([-ShaftSpacing,0,-Spacing+WheelWidth+Over1*2+Clearance1/2]) DriveWheel(DriveWidth);
	}
	for (i=[1:Digits]){
		translate([0,0,(Spacing)*(i-1)]) Assembled_Numbered_Wheels();
	}
	/*For display show only first set of gears (to speed up processing)
	translate([0,0,0]) Assembled_Numbered_Wheels();
	*/
	translate([0,0,-(WheelWidth+DriveWidth)-DriveWidth-Over1]) FeedDriveWheel();
	translate([0,0,-DriveWidth+.1]) SideGear(TeethFeed);
	translate([0,ShaftSpacing,-Over1-WheelWidth-DriveWidth-5]) DriveWheelIdle();
	Odometer_Base();
}
module Parts_Layout(){
	rotate([0,-90,0]) translate([WheelDia/2+Clearance2,0,0]) Odometer_Base();
	for (i=[1:Digits]){
		translate([-(WheelDia+10)*(i-2),BodyWidth,0]) NumberedWheels();
		translate([-(WheelDia+10)*(i-2),BodyWidth+WheelDia+10,0])DriveWheel(DriveWidth);
		translate([-(WheelDia+10)*(i-2),BodyWidth+WheelDia*2+20,0])SideGear(Format);
		translate([-(WheelDia+10)*(i-2),BodyWidth+WheelDia*3+20,0])SideGear(1);
	}
	translate([BodyLength,0,0])SideGear(Format);
	translate([BodyLength+WheelDia+10,0,0])DriveWheelIdle();
	translate([BodyLength+WheelDia+10,WheelDia+10,0])FeedDriveWheel();
}
if (PrintMode==1){
	rotate([0,-90,0]) Full_Assembly();
} else {
	Parts_Layout();
}