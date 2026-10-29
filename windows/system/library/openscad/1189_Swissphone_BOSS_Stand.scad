// [FL_INDEX: keywords="openscad, 3d_parametric, Swissphone_BOSS_Stand, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Swissphone BOSS Stand

rand=1;			//Vertical Wall w/o minkowski sum
breite=53;			//Width ob main block 53sw 53.2bl
dicke=30;			//Thickness of main block
tiefe=12;			//Depth of main block w/o minkowski sum
fuss=1;				//Thickness of lower wall
dicke2=21.20;		//Thickness inner block
minkowskifn=30;	//reduce for speed


difference(){
	union(){
	minkowski(){
		cube([breite+(2*rand),dicke+2*rand,tiefe+fuss]); 					//Main Block	
		sphere(3,$fn=minkowskifn);
	}
	}
	union(){
		translate([rand,rand,fuss])
			cube([breite,dicke2,tiefe+10]);    								//Inner Block
		translate([17,rand+dicke2-0.1,fuss+1])
			cube([23,9,25]);													//Block for the Beltclip
		
		hull(){
			translate([12,5,10+fuss]){											//Frontwindow
				rotate([90,0,0])
				cylinder(h=10,r=7,$fn=50);
			}
			translate([breite-12,5,10+fuss]){
				rotate([90,0,0])
				cylinder(h=10,r=7,$fn=50);
			}
			translate([breite-12,5,10+fuss+20]){
				rotate([90,0,0])
				cylinder(h=10,r=7,$fn=50);
			}
			translate([12,5,10+fuss+20]){
				rotate([90,0,0])
				cylinder(h=10,r=7,$fn=50);
			}
		}											//Holes for Magnets 4mm*10mm (S-04-10-N supermagnete.de)
			//translate([8,27,-5]){
			//	cylinder(h=15,r=2,$fn=50);
			//}
			//translate([47,27,-5]){
			//	cylinder(h=15,r=2,$fn=50);
			//}
			translate([rand+1,dicke2+3,fuss]){
				cube([13,6,12]);
				#cylinder(h=20,r=0.1,$fn=50);
			}
			translate([42,dicke2+3,fuss]){
				cube([10,6,12]);
				#cylinder(h=20,r=0.1,$fn=50);
			}
	}
}
translate([rand,9,fuss])		//Haltestifte
	cube([1,1,12]);
translate([breite,9,fuss])
	cube([1,1,12]);