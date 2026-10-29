// [FL_INDEX: keywords="openscad, 3d_parametric, Gauntlet_Glove, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Gauntlet Glove

//Show (Assembly for visual purposes only)
Show_What="Assembly"; //[Assembly,FullPrint,Fingers,Thumb,Hand,Thumbs_Up]
//Left or Right
Right_or_Left=0; //[0:Right,1:Left]
//Index Finger Length
Index_Finger_Length=90; //[50:110]
//Middle Finger Legnth
Middle_Finger_Length=100; //[50:120]
//Ring Finger Length
Ring_Finger_Length=95; //[50:110]
//Pinky Finger Length
Pinky_Finger_Length=75; //[50:110]
//Average Finger Thickness
Finger_Thickness=20; //[15:25]
//Thumb Length
Thumb_Length=65; //[50:80]
//Distance from Thumb Knuckle to wrist
Thumb_Metacarpal=55; //[50:90]
//Thumb Thickness
Thumb_Thick=20; //[15:25]
//Thumb Joint Length (Adjust this to suit, start with 1/2 Knuckle_Width)
Thumb_Joint_Length=38; //[30:55]
//Thumb Hinge Bearing Size
Thumb_Bearing=7; //[5:15]
//Width of Hand at Knuckles
Knuckle_Width=85; //[65:105]
//Thickness of Hand at Knuckles
Knuckle_Thickness=28; //[20:35]
//Back of Hand Length
Back_Hand_Length=70; //[50:110]
//Wall Thickness
WT=2; //[1:4]
//Pin Radius
PinRad=WT*.75;
//Circle Resolution
CRES=20;
//Fist Angle (Use $t*80 in OpenSCAD for animation)
Fist_Angle=60; //[0:90]

module FingerTip(Length,Thickness){
	difference(){
		union(){
			intersection(){
				cube([Length,Thickness,Thickness],center=true);
				rotate(a=[45,0,0]){cube([Length,Thickness,Thickness],center=true);}
			}
			translate([-Length/2+WT/2,0,0]){rotate(a=[90,0,0]){cylinder(h=Thickness,r=PinRad*2,$fn=CRES,center=true);}}
		}
		translate([Length/2,0,Thickness/2]){rotate(a=[0,20,0]){cube([Length*2,Thickness+WT*2,Thickness*.75],center=true);}}
		translate([-Length/2,0,-Thickness/2]){rotate(a=[0,45,0]){cube([Thickness/2,Thickness+WT*2,Thickness/2],center=true);}}
		translate([-Length/2,0,Thickness/2]){rotate(a=[0,45,0]){cube([Thickness/2,Thickness+WT*2,Thickness/2],center=true);}}
		union(){
			translate([-WT,0,0]){
				difference(){
					intersection(){
						cube([Length,Thickness-WT*2,Thickness-WT*2],center=true);
						rotate(a=[45,0,0]){cube([Length,Thickness-WT*2,Thickness-WT*2],center=true);}
					}
					translate([Length/2,-WT,Thickness/2]){rotate(a=[0,20,0]){cube([Length*2,Thickness+WT*2,Thickness*.75],center=true);}}
				}
			}
		}
		translate([-Length/2+WT/2,0,0]){cube([PinRad*4.25,Thickness-WT*2,PinRad*4],center=true);}
		translate([-Length/2+WT/2,Thickness/2+WT*.1,0]){rotate(a=[90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		translate([-Length/2+WT/2,-Thickness/2-WT*.1,0]){rotate(a=[-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
	}
}
module FingerInter(Length,Thickness){
	difference(){
		union(){
			intersection(){
				cube([Length+PinRad,Thickness,Thickness-WT*2],center=true);
				rotate(a=[45,0,0]){cube([Length+PinRad,Thickness,Thickness],center=true);}
			}
			translate([-Length/2,0,0]){rotate(a=[90,0,0]){cylinder(h=Thickness,r=PinRad*2,$fn=CRES,center=true);}}
			translate([Length/2,0,0]){rotate(a=[90,0,0]){cylinder(h=Thickness,r=PinRad*2,$fn=CRES,center=true);}}
		}
		intersection(){
			cube([Length+WT*2+PinRad*2,Thickness-WT*2,Thickness-WT*4],center=true);
			rotate(a=[45,0,0]){cube([Length+WT*2+PinRad*2,Thickness-WT*2,Thickness-WT*2],center=true);}
		}
		translate([-WT/2,0,Thickness/2-WT]){rotate(a=[45,0,0]){cube([Length+WT*2,Thickness/2+WT,Thickness/2+WT],center=true);}}
		translate([-Length/2,0,-Thickness/2]){rotate(a=[0,45,0]){cube([Thickness,Thickness+WT*2,Thickness/2-PinRad/2],center=true);}}
		translate([-Length/2,0,Thickness/2]){rotate(a=[0,-45,0]){cube([Thickness,Thickness+WT*2,Thickness/2-PinRad/2],center=true);}}
		translate([Length/2,0,-Thickness/2]){rotate(a=[0,-45,0]){cube([Thickness,Thickness+WT*2,Thickness/2-PinRad/2],center=true);}}
		translate([Length/2,0,Thickness/2]){rotate(a=[0,45,0]){cube([Thickness,Thickness+WT*2,Thickness/2-PinRad/2],center=true);}}
	}
	translate([Length/2,Thickness/2-WT,0]){rotate(a=[90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
	translate([-Length/2,Thickness/2-WT,0]){rotate(a=[90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
	translate([Length/2,-Thickness/2+WT,0]){rotate(a=[-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
	translate([-Length/2,-Thickness/2+WT,0]){rotate(a=[-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
}
module FingerProxi(Length,Thickness,Finger){
	difference(){
		union(){
			intersection(){
				cube([Length,Thickness,Thickness],center=true);
				rotate(a=[45,0,0]){cube([Length,Thickness,Thickness],center=true);}
			}
			translate([+Length/2,0,0]){rotate(a=[90,0,0]){cylinder(h=Thickness,r=PinRad*2,$fn=CRES,center=true);}}
			translate([-Length/2,0,-Thickness/2]){cylinder(r=PinRad*2,h=WT,$fn=CRES);}
		}
		intersection(){
			cube([Length+WT*2+PinRad*2,Thickness-WT*2,Thickness-WT*2],center=true);
			rotate(a=[45,0,0]){cube([Length+WT*2+PinRad*2,Thickness-WT*2,Thickness-WT*2],center=true);}
		}
		translate([Length/2+PinRad,0,-Thickness/2]){rotate(a=[0,45,0]){cube([Thickness/2,Thickness+WT*2,Thickness/2],center=true);}}
		translate([Length/2,0,Thickness/2]){rotate(a=[0,45,0]){cube([Thickness/2,Thickness+WT*2,Thickness/2],center=true);}}
		translate([-WT/2,0,Thickness/2-WT]){rotate(a=[45,0,0]){cube([Length+WT*2,Thickness/2+WT,Thickness/2+WT],center=true);}}
		if(Finger=="Index"){
			translate([-WT-Length/4,Thickness/2-WT,0]){rotate(a=[45,0,0]){cube([Length+WT,Thickness/2+WT,Thickness/2+WT],center=true);}}
			translate([-WT-Length/4,-Thickness/2+WT,0]){rotate(a=[45,0,0]){cube([Length/2+WT,Thickness/2+WT,Thickness/2+WT],center=true);}}
		}else if(Finger=="Pinky"){
			translate([-WT-Length/4,-Thickness/2+WT,0]){rotate(a=[45,0,0]){cube([Length+WT,Thickness/2+WT,Thickness/2+WT],center=true);}}
			translate([-WT-Length/4,+Thickness/2-WT,0]){rotate(a=[45,0,0]){cube([Length/2+WT,Thickness/2+WT,Thickness/2+WT],center=true);}}
		}else{
			translate([-WT-Length/4,Thickness/2-WT,0]){rotate(a=[45,0,0]){cube([Length+WT,Thickness/2+WT,Thickness/2+WT],center=true);}}
			translate([-WT-Length/4,-Thickness/2+WT,0]){rotate(a=[45,0,0]){cube([Length+WT,Thickness/2+WT,Thickness/2+WT],center=true);}}
		}
		translate([-WT-Length/4,0,0]){cube([Length/2+WT,Thickness+WT,Thickness-WT*2],center=true);}
		translate([Length/2,Thickness/2+WT*.1,0]){rotate(a=[90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		translate([Length/2,-Thickness/2-WT*.1,0]){rotate(a=[-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		translate([-Length/2,0,-Thickness/2-WT*.1]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}
	}
	translate([-Length/2,0,-Thickness/2+WT]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}
}
module KnuckleGuard(Width,Thickness,F_Thick){
	union(){
		difference(){
			union(){
				translate([0,-Width/2-WT,0]){cube([Thickness*.75,WT,Thickness/2+PinRad*2]);}
				translate([0,Width/2,0]){cube([Thickness*.75,WT,Thickness/2+PinRad*2]);}
			}
			translate([Thickness/2,Width/2+WT*1.1,Thickness/2-WT*3]){rotate([90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
			translate([Thickness/2,-Width/2-WT*1.1,Thickness/2-WT*3]){rotate([-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
			translate([0,0,Thickness/2+PinRad*2]){rotate(a=[0,45,0]){cube([Thickness/3,Width+WT*3,Thickness/3],center=true);}}
		}
		difference(){
			translate([0,-Width/2,0]){cube([Thickness*.75,Width,WT]);}
			//Locating Pins for Fingers
			translate([Thickness/2,-F_Thick*.5-WT/2,-WT*.1]){rotate([0,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
			translate([Thickness/2,F_Thick*.5+WT/2,-WT*.1]){rotate([0,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
			translate([Thickness/2,-F_Thick*1.5-WT*2,-WT*.1]){rotate([0,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
			translate([Thickness/2,F_Thick*1.5+WT*2,-WT*.1]){rotate([0,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		}
		//Locating Pins for Fingers
		translate([Thickness/2,-F_Thick*.5-WT/2,-WT]){rotate([0,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		translate([Thickness/2,F_Thick*.5+WT/2,-WT]){rotate([0,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		translate([Thickness/2,-F_Thick*1.5-WT*2,-WT]){rotate([0,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		translate([Thickness/2,F_Thick*1.5+WT*2,-WT]){rotate([0,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		//Top Clip for Fingers
		translate([0,-Width/2,-WT*2]){cube([Thickness/2+PinRad*2,Width,WT]);}
		translate([0,-Width/2,-WT]){cube([WT*3,Width,WT]);}
	}
}
module BackHand(Length,Width,Thickness,F_Thick){
	difference(){
		union(){
			difference(){
				difference(){
					cube([Length,Width,Thickness/2+PinRad*2]);
					translate([-WT*.1,-WT*.1,Thickness/2+PinRad*2+WT*.1]){
						polyhedron(
							points=[[0,0,0],[0,Thickness/3,0],[0,0,-Thickness/3],[Length,0,0]],
							triangles=[[2,1,0],[1,3,0],[2,0,3],[3,1,2]]
						);
					}
				}
				difference(){
					translate([-WT*.1,WT,-WT]){cube([Length+WT*.2,Width-WT*2,Thickness/2+PinRad*2]);}
					translate([-WT*.4,-WT*.4+WT*1,Thickness/2+PinRad*2+WT*.1-WT]){
						polyhedron(
							points=[[0,0,0],[0,Thickness/3,0],[0,0,-Thickness/3],[Length,0,0]],
							triangles=[[2,1,0],[1,3,0],[2,0,3],[3,1,2]]
						);
					}
				}
				difference(){
					translate([-WT*.1,Width*.6+WT*.1,-WT*.5]){cube([Length-Thickness/2,Width*.6,Thickness/2+PinRad*2+WT]);}
					translate([Length-Thickness/2,Width*.6+WT*.1,(Thickness/2+PinRad*2+WT/2)/2]){rotate(a=[0,0,45]){cube([Thickness,Thickness,Thickness/2+PinRad*2+WT],center=true);}}
				}
			}
			translate([Length,0,0]){cube([Thickness/2+PinRad*2,WT,Thickness/2+PinRad*2]);}
			translate([Length,Width-WT,0]){cube([Thickness/2+PinRad*2,WT,Thickness/2+PinRad*2]);}
			translate([Length+Thickness/2,WT,(Thickness/2+PinRad*2)-F_Thick/2+PinRad*1.25]){rotate([-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
			translate([Length+Thickness/2,Width-WT,(Thickness/2+PinRad*2)-F_Thick/2+PinRad*1.25]){rotate([90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
			//Place locating pins
			translate([Length/8,WT,PinRad*2]){rotate([-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
			translate([Length*3/8,WT,PinRad*2]){rotate([-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
			translate([Length*5/8,WT,PinRad*2]){rotate([-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
			translate([Length*7/8,WT,PinRad*2]){rotate([-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
			translate([Length*7/8,Width-WT,PinRad*2]){rotate([90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
			//Place locating hubs
			translate([0,Width*.6+WT*.1-Thumb_Bearing*1.25,Thickness/2+PinRad*2-Thumb_Bearing*3/8]){cube([Thumb_Bearing*1.25,Thumb_Bearing*1.25,Thumb_Bearing*3/8]);}
			translate([Thumb_Bearing*3.5,Width*.6+WT*.1-Thumb_Bearing*1.25,Thickness/2+PinRad*2-Thumb_Bearing*3/8]){cube([Thumb_Bearing*1.25,Thumb_Bearing*1.25,Thumb_Bearing*3/8]);}
		}
		translate([Thumb_Bearing*5/8,Width*.6+WT*.1-Thumb_Bearing*5/8,Thickness/2+PinRad*2-Thumb_Bearing*3/16]){sphere(r=Thumb_Bearing/2,$fn=CRES);}
		translate([Thumb_Bearing*3.5+Thumb_Bearing*5/8,Width*.6+WT*.1-Thumb_Bearing*5/8,Thickness/2+PinRad*2-Thumb_Bearing*3/16]){sphere(r=Thumb_Bearing/2,$fn=CRES);}
		translate([Thumb_Bearing*5/8,Width*.6+WT*.1-Thumb_Bearing*5/8,Thickness/2+PinRad*2-Thumb_Bearing*3/16]){cube([Thumb_Bearing*3/8,Thumb_Bearing*2,Thumb_Bearing/2],center=true);}
		translate([Thumb_Bearing*3.5+Thumb_Bearing*5/8,Width*.6+WT*.1-Thumb_Bearing*5/8,Thickness/2+PinRad*2-Thumb_Bearing*3/16]){cube([Thumb_Bearing*3/8,Thumb_Bearing*2,Thumb_Bearing/2],center=true);}
	}
}
module Palm(Length,Width,Thickness,F_Thick){
	difference(){
		difference(){
			cube([Length,Width,Thickness/2+PinRad*4]);
			translate([-WT*.1,-WT*.1,Thickness/2+PinRad*4+WT*.1]){
				polyhedron(
					points=[[0,0,0],[0,Thickness/3,0],[0,0,-Thickness/3],[Length,0,0]],
					triangles=[[2,1,0],[1,3,0],[2,0,3],[3,1,2]]
				);
			}
		}
		difference(){
			translate([-WT*.1,WT,-WT]){cube([Length+WT*.2,Width-WT*2,Thickness/2+PinRad*4]);}
			translate([-WT*.4,-WT*.4+WT*1,Thickness/2+PinRad*4+WT*.1-WT]){
				polyhedron(
					points=[[0,0,0],[0,Thickness/3,0],[0,0,-Thickness/3],[Length,0,0]],
					triangles=[[2,1,0],[1,3,0],[2,0,3],[3,1,2]]
				);
			}
		}
		difference(){
			translate([-WT*.1,Width*.3+WT*.1,-WT*.5]){cube([Length-Thickness/2,Width*.7,Thickness/2+PinRad*4+WT]);}
			translate([Length-Thickness/2,Width*.3+WT*.1,(Thickness/2+PinRad*4+WT/2)/2]){rotate(a=[0,0,45]){cube([Thickness,Thickness,Thickness/2+PinRad*4+WT],center=true);}}
		}
		translate([Length/8,-WT*.1,PinRad*2]){rotate([-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		translate([Length*3/8,-WT*.1,PinRad*2]){rotate([-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		translate([Length*5/8,-WT*.1,PinRad*2]){rotate([-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		translate([Length*7/8,-WT*.1,PinRad*2]){rotate([-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		translate([Length*7/8,Width+WT*.1,PinRad*2]){rotate([90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		translate([Length,Width/2,0]){rotate(a=[0,45,0]){cube([Thickness/3,Width+WT,Thickness/3],center=true);}}
	}
}
module ThumbProxi(Length,Thickness){
	difference(){
		union(){
			intersection(){
				cube([Length+PinRad,Thickness,Thickness-WT*2],center=true);
				rotate(a=[45,0,0]){cube([Length+PinRad,Thickness,Thickness],center=true);}
			}
			translate([-Length/2,0,0]){rotate(a=[90,0,0]){cylinder(h=Thickness,r=PinRad*2,$fn=CRES,center=true);}}
			translate([Length/2,0,0]){rotate(a=[90,0,0]){cylinder(h=Thickness,r=PinRad*2,$fn=CRES,center=true);}}
		}
		intersection(){
			cube([Length+WT*2+PinRad*2,Thickness-WT*2,Thickness-WT*4],center=true);
			rotate(a=[45,0,0]){cube([Length+WT*2+PinRad*2,Thickness-WT*2,Thickness-WT*2],center=true);}
		}
		translate([-WT/2,0,Thickness/2-WT]){rotate(a=[45,0,0]){cube([Length+WT*2,Thickness/2+WT,Thickness/2+WT],center=true);}}
		translate([-Length/2,0,-Thickness/2]){rotate(a=[0,45,0]){cube([Thickness,Thickness+WT*2,Thickness/2-PinRad/2],center=true);}}
		translate([-Length/2,0,Thickness/2]){rotate(a=[0,-45,0]){cube([Thickness,Thickness+WT*2,Thickness/2-PinRad/2],center=true);}}
		translate([Length/2,0,-Thickness/2]){rotate(a=[0,-45,0]){cube([Thickness,Thickness+WT*2,Thickness/2-PinRad/2],center=true);}}
		translate([Length/2,0,Thickness/2]){rotate(a=[0,45,0]){cube([Thickness,Thickness+WT*2,Thickness/2-PinRad/2],center=true);}}
		translate([-Length*.4,Thickness/3,Thickness/3]){cube([Length,Thickness/2,Thickness],center=true);}
	}
	translate([Length/2,Thickness/2-WT,0]){rotate(a=[90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
	translate([-Length/2,-Thickness/2+WT,0]){rotate(a=[-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
	translate([Length/2,-Thickness/2+WT,0]){rotate(a=[-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
	translate([-Length/2,-Thickness/2,0]){rotate(a=[90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
}
module ThumbMeta(Length,Thickness){
	translate([0,-WT*2,0]){
		difference(){
			union(){
				intersection(){
					cube([Length+PinRad,Thickness,Thickness],center=true);
					rotate(a=[45,0,0]){cube([Length+PinRad,Thickness,Thickness],center=true);}
				}
				//translate([-Length/2,0,0]){rotate(a=[90,0,0]){cylinder(h=Thickness,r=PinRad*2,$fn=CRES,center=true);}}
				translate([Length/2,0,0]){rotate(a=[90,0,0]){cylinder(h=Thickness,r=PinRad*2,$fn=CRES,center=true);}}
			}
			intersection(){
				cube([Length+WT*2+PinRad*2,Thickness-WT*2,Thickness-WT*2],center=true);
				rotate(a=[45,0,0]){cube([Length+WT*2+PinRad*2,Thickness-WT*2,Thickness-WT*2],center=true);}
			}
		translate([0,-Thickness,PinRad*2+Thickness/2]){rotate(a=[-45,0,0]){cube([Length,Thickness*2,Thickness]);}}
		translate([Length/2,0,-Thickness/2]){rotate(a=[0,-45,0]){cube([Thickness,Thickness+WT*2,Thickness/2-PinRad/2],center=true);}}
		translate([-Length/2,0,0]){rotate(a=[0,-45,0]){cube([Length*2,Thickness+WT*2,Length],center=true);}}
		translate([Length/2,-Thickness/2+WT*1.1,0]){rotate(a=[90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		}
	}
	difference(){
		union(){
			intersection(){
				cube([Length+PinRad,Thickness,Thickness],center=true);
				rotate(a=[45,0,0]){cube([Length+PinRad,Thickness,Thickness],center=true);}
			}
			//translate([-Length/2,0,0]){rotate(a=[90,0,0]){cylinder(h=Thickness,r=PinRad*2,$fn=CRES,center=true);}}
			translate([Length/2,0,0]){rotate(a=[90,0,0]){cylinder(h=Thickness,r=PinRad*2,$fn=CRES,center=true);}}
		}
		intersection(){
			cube([Length+WT*2+PinRad*2,Thickness-WT*2,Thickness-WT*2],center=true);
			rotate(a=[45,0,0]){cube([Length+WT*2+PinRad*2,Thickness-WT*2,Thickness-WT*2],center=true);}
		}
		translate([Length/2,-Thickness/2-WT*.1,0]){rotate(a=[-90,0,0]){cylinder(r1=PinRad*1.25,r2=PinRad*.25,h=PinRad,$fn=CRES);}}
		translate([Length/2,0,-Thickness/2]){rotate(a=[0,-45,0]){cube([Thickness,Thickness+WT*2,Thickness/2-PinRad/2],center=true);}}
		translate([Length/2,0,Thickness/2]){rotate(a=[0,45,0]){cube([Thickness,Thickness+WT*2,Thickness/2-PinRad/2],center=true);}}
		translate([-Length/2-WT,Thickness/2,-Thickness/2]){rotate(a=[45,0,0]){cube([Length+WT*2+PinRad*2,Thickness,Thickness*2]);}}
	}
	difference(){
		translate([-Length/2,WT,-Thickness/2]){rotate(a=[-45,0,0]){cube([Length-Thickness/2,Thumb_Bearing*3/8,Thickness]);}}
		translate([0,0,-Thickness]){cube([Length+PinRad,Thickness,Thickness],center=true);}
		translate([-Length/2+Thumb_Bearing*.8,WT,-Thickness/2]){
			rotate(a=[-45,0,0]){translate([0,Thumb_Bearing*3/16,Thickness-Thumb_Bearing*.8]){
				sphere(r=Thumb_Bearing/2,$fn=CRES);
				translate([-Thumb_Bearing*3/16,-Thumb_Bearing*4/16,-Thumb_Bearing]){cube([Thumb_Bearing*3/8,Thumb_Bearing*4/8,Thumb_Bearing*2]);}
		}}}
	}
}
module ThumbConnect(){
	//Place Balls
	translate([0,0,Thumb_Bearing*11/8]){sphere(r=Thumb_Bearing/2,$fn=CRES);}
	translate([Thumb_Bearing*3.5,0,Thumb_Bearing*11/8]){sphere(r=Thumb_Bearing/2,$fn=CRES);}
	translate([-Thumb_Bearing*5/8,-Thumb_Joint_Length,Thumb_Bearing*11/8]){sphere(r=Thumb_Bearing/2,$fn=CRES);}
	//Place Rods
	translate([0,0,0]){cylinder(r=Thumb_Bearing*3/8,h=Thumb_Bearing*11/8,$fn=CRES);}
	translate([Thumb_Bearing*3.5,0,0]){cylinder(r=Thumb_Bearing*3/8,h=Thumb_Bearing*11/8,$fn=CRES);}
	translate([-Thumb_Bearing*5/8,-Thumb_Joint_Length,0]){cylinder(r=Thumb_Bearing*3/8,h=Thumb_Bearing*11/8,$fn=CRES);}
	//Place Cover
	translate([-Thumb_Bearing*5/8-Thumb_Bearing,-Thumb_Joint_Length-Thumb_Bearing,0]){cube([Thumb_Bearing*3.5+Thumb_Bearing*5/8+Thumb_Bearing*2,Thumb_Joint_Length+Thumb_Bearing*2,Thumb_Bearing*3/8]);}
}

module FullHand(){
	//Index Finger
	translate([0,-Finger_Thickness*1.5-WT*2,0]){rotate(a=[0,0,-12]){
		translate([Index_Finger_Length*7/8,0,0]){FingerTip(Index_Finger_Length/4+WT,Finger_Thickness);} //Distal Phalanges
		translate([Index_Finger_Length*5/8,0,0]){FingerInter(Index_Finger_Length/4,Finger_Thickness+WT*2);} //Intermediate Phalanges
		translate([Index_Finger_Length/4,0,0]){FingerProxi(Index_Finger_Length/2,Finger_Thickness,"Index");} //Proximal Phalanges
	}}
	//Middle Finger
	translate([0,-Finger_Thickness*.5-WT/2,0]){rotate(a=[0,0,-5]){
		translate([Middle_Finger_Length*7/8,0,0]){FingerTip(Middle_Finger_Length/4+WT,Finger_Thickness);} //Distal Phalanges
		translate([Middle_Finger_Length*5/8,0,0]){FingerInter(Middle_Finger_Length/4,Finger_Thickness+WT*2);} //Intermediate Phalanges
		translate([Middle_Finger_Length/4,0,0]){FingerProxi(Middle_Finger_Length/2,Finger_Thickness,"Middle");} //Proximal Phalanges
	}}
	//Ring Finger
	translate([0,Finger_Thickness*.5+WT/2,0]){rotate(a=[0,0,5]){
		translate([Ring_Finger_Length*7/8,0,0]){FingerTip(Ring_Finger_Length/4+WT,Finger_Thickness);} //Distal Phalanges
		translate([Ring_Finger_Length*5/8,0,0]){FingerInter(Ring_Finger_Length/4,Finger_Thickness+WT*2);} //Intermediate Phalanges
		translate([Ring_Finger_Length/4,0,0]){FingerProxi(Ring_Finger_Length/2,Finger_Thickness,"Ring");} //Proximal Phalanges
	}}
	//Pinky Finger
	translate([0,Finger_Thickness*1.5+WT*2,0]){rotate(a=[0,0,12]){
		translate([Pinky_Finger_Length*7/8,0,0]){FingerTip(Pinky_Finger_Length/4+WT,Finger_Thickness);} //Distal Phalanges
		translate([Pinky_Finger_Length*5/8,0,0]){FingerInter(Pinky_Finger_Length/4,Finger_Thickness+WT*2);} //Intermediate Phalanges
		translate([Pinky_Finger_Length/4,0,0]){FingerProxi(Pinky_Finger_Length/2,Finger_Thickness,"Pinky");} //Proximal Phalanges
	}}
	//Place Knuckles
	translate([-Knuckle_Thickness/2,0,-Finger_Thickness/2+WT]){
		KnuckleGuard(Knuckle_Width,Knuckle_Thickness,Finger_Thickness);
	}
	//Place Back of Hand
	translate([-Back_Hand_Length-Knuckle_Thickness/2,Knuckle_Width/2+WT*2,PinRad*2+WT*3]){rotate(a=[180,0,0]){
		BackHand(Back_Hand_Length,Knuckle_Width+WT*4,Knuckle_Thickness,Finger_Thickness);
	}}
	//Place Palm of Hand
	translate([-Back_Hand_Length-Knuckle_Thickness/2,Knuckle_Width/2+WT,-PinRad*2+WT*3]){rotate(a=[0,0,0]){
		mirror([0,1,0]){Palm(Back_Hand_Length,Knuckle_Width+WT*2.05,Knuckle_Thickness,Finger_Thickness);}
	}}
	//Place Thumb (-Knuckle_Width/2)
	translate([-Back_Hand_Length-Knuckle_Thickness/2,-Thumb_Joint_Length+(Knuckle_Width/2+WT*2-((Knuckle_Width+WT*4)*.6+WT*.1)+Thumb_Bearing*5/8),Thumb_Bearing*3/16+WT*3-Knuckle_Thickness/2]){rotate(a=[0,0,-30]){
		rotate(a=[-90,0,0]){translate([+Thumb_Metacarpal/2-Thumb_Bearing*.8,-Thumb_Bearing*3/16,-(Thumb_Thick+WT*2)+Thumb_Bearing*.8]){rotate(a=[45,0,0]){
			translate([0,-WT,(Thumb_Thick+WT*2)/2]){ThumbMeta(Thumb_Metacarpal,Thumb_Thick+WT*2);}
			translate([Thumb_Length*5/6+Thumb_Metacarpal/2,-WT,(Thumb_Thick+WT*2)/2]){FingerTip(Thumb_Length/3+WT,Thumb_Thick+WT*2);}
			translate([Thumb_Length*2/6+Thumb_Metacarpal/2,-WT,(Thumb_Thick+WT*2)/2]){ThumbProxi(Thumb_Length*2/3,Thumb_Thick+WT*4);}
		}}}
	}}
	//Place Thumb connector
	translate([-Back_Hand_Length-Knuckle_Thickness/2+Thumb_Bearing*5/8,Knuckle_Width/2+WT*2-((Knuckle_Width+WT*4)*.6+WT*.1)+Thumb_Bearing*5/8,Thumb_Bearing*3/16+WT*3-Knuckle_Thickness/2-Thumb_Bearing*11/8]){ThumbConnect();}
}
module Hand(){
	//Place Back of Hand
	translate([-PinRad*3,0,Knuckle_Thickness/2+PinRad*2]){rotate(a=[180,0,-90]){
		BackHand(Back_Hand_Length,Knuckle_Width+WT*4,Knuckle_Thickness,Finger_Thickness);
	}}
	//Place Palm of Hand
	translate([-PinRad*3,WT,Knuckle_Thickness/2+PinRad*4]){rotate(a=[180,0,90]){
		mirror([0,1,0]){Palm(Back_Hand_Length,Knuckle_Width+WT*2.05,Knuckle_Thickness,Finger_Thickness);}
	}}
	//Place Thumb connector
	translate([Thumb_Bearing*1.5+WT*2,-Thumb_Bearing-Finger_Thickness-WT*2,0]){rotate(a=[0,0,0]){ThumbConnect();}}
}
module Thumb(){
	//Place Thumb (-Knuckle_Width/2)
	translate([0,0,0]){rotate(a=[0,0,0]){
		translate([-Knuckle_Width,Thumb_Metacarpal/2+WT,Thumb_Thick/2+WT]){rotate(a=[0,0,90]){ThumbMeta(Thumb_Metacarpal,Thumb_Thick+WT*2);}}
		translate([-Knuckle_Width/2,Thumb_Thick,Thumb_Length/6+WT/2]){rotate(a=[0,90,0]){FingerTip(Thumb_Length/3+WT,Thumb_Thick+WT*2);}}
		translate([-Knuckle_Width,-Thumb_Length*2/6-WT,Thumb_Thick/2+WT]){rotate(a=[0,0,90]){ThumbProxi(Thumb_Length*2/3,Thumb_Thick+WT*4);}}
	}}
}
module Fingers(){
	//Index Finger
	translate([0,0,0]){rotate(a=[0,0,0]){
		translate([Index_Finger_Length*5/8+PinRad*6+Finger_Thickness+WT,0,Index_Finger_Length/8+WT/2]){rotate(a=[0,90,0]){FingerTip(Index_Finger_Length/4+WT,Finger_Thickness);}} //Distal Phalanges
		translate([Index_Finger_Length*5/8+PinRad*6,0,Finger_Thickness/2]){FingerInter(Index_Finger_Length/4,Finger_Thickness+WT*2);} //Intermediate Phalanges
		translate([Index_Finger_Length*1/4,0,Finger_Thickness/2]){FingerProxi(Index_Finger_Length/2,Finger_Thickness,"Index");} //Proximal Phalanges
	}}
	//Middle Finger
	translate([0,Finger_Thickness+WT*4,0]){rotate(a=[0,0,0]){
		translate([Middle_Finger_Length*5/8+PinRad*6+Finger_Thickness+WT,0,Middle_Finger_Length/8+WT/2]){rotate(a=[0,90,0]){FingerTip(Middle_Finger_Length/4+WT,Finger_Thickness);}} //Distal Phalanges
		translate([Middle_Finger_Length*5/8+PinRad*6,0,Finger_Thickness/2]){FingerInter(Middle_Finger_Length/4,Finger_Thickness+WT*2);} //Intermediate Phalanges
		translate([Middle_Finger_Length*1/4,0,Finger_Thickness/2]){FingerProxi(Middle_Finger_Length/2,Finger_Thickness,"Middle");} //Proximal Phalanges
	}}
	//Ring Finger
	translate([0,(Finger_Thickness+WT*4)*2,0]){rotate(a=[0,0,0]){
		translate([Ring_Finger_Length*5/8+PinRad*6+Finger_Thickness+WT,0,Ring_Finger_Length/8+WT/2]){rotate(a=[0,90,0]){FingerTip(Ring_Finger_Length/4+WT,Finger_Thickness);}} //Distal Phalanges
		translate([Ring_Finger_Length*5/8+PinRad*6,0,Finger_Thickness/2]){FingerInter(Ring_Finger_Length/4,Finger_Thickness+WT*2);} //Intermediate Phalanges
		translate([Ring_Finger_Length*1/4,0,Finger_Thickness/2]){FingerProxi(Ring_Finger_Length/2,Finger_Thickness,"Ring");} //Proximal Phalanges
	}}
	//Pinky Finger
	translate([0,(Finger_Thickness+WT*4)*3,0]){rotate(a=[0,0,0]){
		translate([Pinky_Finger_Length*5/8+PinRad*6+Finger_Thickness+WT,0,Pinky_Finger_Length/8+WT/2]){rotate(a=[0,90,0]){FingerTip(Pinky_Finger_Length/4+WT,Finger_Thickness);}} //Distal Phalanges
		translate([Pinky_Finger_Length*5/8+PinRad*6,0,Finger_Thickness/2]){FingerInter(Pinky_Finger_Length/4,Finger_Thickness+WT*2);} //Intermediate Phalanges
		translate([Pinky_Finger_Length*1/4,0,Finger_Thickness/2]){FingerProxi(Pinky_Finger_Length/2,Finger_Thickness,"Pinky");} //Proximal Phalanges
	}}
	//Place Knuckles
	translate([Knuckle_Width/2+WT,-Finger_Thickness,0]){rotate(a=[0,-90,90]){
		KnuckleGuard(Knuckle_Width,Knuckle_Thickness,Finger_Thickness);
	}}
}

module Thumbs_Up(){
	rotate(a=[0,-Fist_Angle,0]){
		//Index Finger
		translate([0,-Finger_Thickness*1.5-WT*2,0]){rotate(a=[0,0,-12]){
			translate([Index_Finger_Length/4,0,0]){FingerProxi(Index_Finger_Length/2,Finger_Thickness,"Index");}
			translate([Index_Finger_Length/2,0,0]){rotate(a=[0,-Fist_Angle,0]){translate([Index_Finger_Length*1/8,0,0]){FingerInter(Index_Finger_Length/4,Finger_Thickness+WT*2);}
			translate([Index_Finger_Length/4,0,0]){rotate(a=[0,-Fist_Angle,0]){translate([Index_Finger_Length*1/8,0,0]){FingerTip(Index_Finger_Length/4+WT,Finger_Thickness);}
			}}}}
		}}
		//Middle Finger
		translate([0,-Finger_Thickness*.5-WT/2,0]){rotate(a=[0,0,-5]){
			translate([Middle_Finger_Length/4,0,0]){FingerProxi(Middle_Finger_Length/2,Finger_Thickness,"Middle");}
			translate([Middle_Finger_Length/2,0,0]){rotate(a=[0,-Fist_Angle,0]){translate([Middle_Finger_Length*1/8,0,0]){FingerInter(Middle_Finger_Length/4,Finger_Thickness+WT*2);}
			translate([Middle_Finger_Length/4,0,0]){rotate(a=[0,-Fist_Angle,0]){translate([Middle_Finger_Length*1/8,0,0]){FingerTip(Middle_Finger_Length/4+WT,Finger_Thickness);}
			}}}}
		}}
		//Ring Finger
		translate([0,Finger_Thickness*.5+WT/2,0]){rotate(a=[0,0,5]){
			translate([Ring_Finger_Length/4,0,0]){FingerProxi(Ring_Finger_Length/2,Finger_Thickness,"Ring");}
			translate([Ring_Finger_Length/2,0,0]){rotate(a=[0,-Fist_Angle,0]){translate([Ring_Finger_Length*1/8,0,0]){FingerInter(Ring_Finger_Length/4,Finger_Thickness+WT*2);}
			translate([Ring_Finger_Length/4,0,0]){rotate(a=[0,-Fist_Angle,0]){translate([Ring_Finger_Length*1/8,0,0]){FingerTip(Ring_Finger_Length/4+WT,Finger_Thickness);}
			}}}}
		}}
		//Pinky Finger
		translate([0,Finger_Thickness*1.5+WT*2,0]){rotate(a=[0,0,12]){
			translate([Pinky_Finger_Length/4,0,0]){FingerProxi(Pinky_Finger_Length/2,Finger_Thickness,"Pinky");}
			translate([Pinky_Finger_Length/2,0,0]){rotate(a=[0,-Fist_Angle,0]){translate([Pinky_Finger_Length*1/8,0,0]){FingerInter(Pinky_Finger_Length/4,Finger_Thickness+WT*2);}
			translate([Pinky_Finger_Length/4,0,0]){rotate(a=[0,-Fist_Angle,0]){translate([Pinky_Finger_Length*1/8,0,0]){FingerTip(Pinky_Finger_Length/4+WT,Finger_Thickness);}
			}}}}
		}}
		//Place Knuckles
		translate([-Knuckle_Thickness/2,0,-Finger_Thickness/2+WT]){
			KnuckleGuard(Knuckle_Width,Knuckle_Thickness,Finger_Thickness);
		}
	}
	//Place Back of Hand
	translate([-Back_Hand_Length-Knuckle_Thickness/2,Knuckle_Width/2+WT*2,PinRad*2+WT*3]){rotate(a=[180,0,0]){
		BackHand(Back_Hand_Length,Knuckle_Width+WT*4,Knuckle_Thickness,Finger_Thickness);
	}}
	//Place Palm of Hand
	translate([-Back_Hand_Length-Knuckle_Thickness/2,Knuckle_Width/2+WT,-PinRad*2+WT*3]){rotate(a=[0,0,0]){
		mirror([0,1,0]){Palm(Back_Hand_Length,Knuckle_Width+WT*2.05,Knuckle_Thickness,Finger_Thickness);}
	}}
	//Place Thumb (-Knuckle_Width/2)
	translate([-Back_Hand_Length-Knuckle_Thickness/2,-Thumb_Joint_Length+(Knuckle_Width/2+WT*2-((Knuckle_Width+WT*4)*.6+WT*.1)+Thumb_Bearing*5/8),Thumb_Bearing*3/16+WT*3-Knuckle_Thickness/2]){rotate(a=[0,0,-45]){
		rotate(a=[-90,0,0]){translate([+Thumb_Metacarpal/2-Thumb_Bearing*.8,-Thumb_Bearing*3/16,-(Thumb_Thick+WT*2)+Thumb_Bearing*.8]){rotate(a=[45,0,0]){
			translate([0,-WT,(Thumb_Thick+WT*2)/2]){ThumbMeta(Thumb_Metacarpal,Thumb_Thick+WT*2);}
			translate([Thumb_Length*5/6+Thumb_Metacarpal/2,-WT,(Thumb_Thick+WT*2)/2]){FingerTip(Thumb_Length/3+WT,Thumb_Thick+WT*2);}
			translate([Thumb_Length*2/6+Thumb_Metacarpal/2,-WT,(Thumb_Thick+WT*2)/2]){ThumbProxi(Thumb_Length*2/3,Thumb_Thick+WT*4);}
		}}}
	}}
	//Place Thumb connector
	translate([-Back_Hand_Length-Knuckle_Thickness/2+Thumb_Bearing*5/8,Knuckle_Width/2+WT*2-((Knuckle_Width+WT*4)*.6+WT*.1)+Thumb_Bearing*5/8,Thumb_Bearing*3/16+WT*3-Knuckle_Thickness/2-Thumb_Bearing*11/8]){ThumbConnect();}
}

mirror([0,Right_or_Left,0]){
	//Assembly,FullPrint,Fingers,Thumb,Hand
	if(Show_What=="Assembly"){
		rotate(a=[-90,0,0]){FullHand();}
	}else if(Show_What=="FullPrint"){
		Fingers();
		Hand();
		Thumb();
	}else if(Show_What=="Fingers"){
		Fingers();
	}else if (Show_What=="Thumb"){
		Thumb();
	}else if (Show_What=="Hand"){
		Hand();
	}else if (Show_What=="Thumbs_Up"){
		rotate(a=[-90,0,0]){Thumbs_Up();}
	}
}