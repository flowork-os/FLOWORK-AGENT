// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_Turret_2_0, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable Turret 2.0

//Created by Ari M. Diacou, February 2014
//Shared under Creative Commons License: Attribution 3.0 Unported (CC BY-SA 3.0) 
//see http://creativecommons.org/licenses/by-sa/3.0/

/* [Base] */
//A way to save your "random" arrangement
master_seed=13;
//Number of intersections forming a block
n=8;
//reduces the ablity of higher n to cut away all the block, I like -0.4.
power=-.4; //[-1,-0.9,-0.8,-0.7,-0.6,-0.5,-0.4,-0.3,-0.2,-0.1,0]
//Maximum angle of block intersections
max_angle=15;
//How many blocks form a circle?
blocks_per_rev=12;
//Number of layers of blocks in the turret base
height=6;
//The height of each block in mm
block_height=4;
//The radial width of a block in mm
block_thickness=10;
//The internal radius of the turret in mm
turret_radius=25;
//How much curviness do you want?
$fn=30;
//<1 Compresses layers, >1 expands them to show mortar
z_spacing=1.1;
//<1 Compresses layers, >1 expands them to show mortar
theta_expansion=1.0;
//Mortar thickeness divided by Block thickness, if you dont want, hit zero.
mortar_thickness=.4;

/* [Top] */
//Do you want a top?
care="yes";//[yes,no]
//Do 45 degree overhangs scare you?
noob="no";//[yes,no]
//How many blocks wide do you want the lookout stones?
factor=1.5;

/* [Hidden] */
stone="silver";
grout="ghostwhite";
rad=turret_radius;
num=blocks_per_rev;
union(){
	color(stone) base();
	if(mortar_thickness>.01){
		color(grout) 
			mortar(turret_radius,mortar_thickness);
		}
	}
if (care=="yes") {crown();}

module crown(){
	phase=360/num*(ceil(factor)-factor)/1;
	if(noob=="no"){
		translate([2*rad+4*block_thickness,0,3*block_height]) union(){
			//The conical base
			translate([0,0,-3*block_height]) 
				color(stone) cylinder(2*block_height,turret_radius+block_thickness,turret_radius+2*block_thickness);
			//The middle stones
			for(i=[1:num]){
				rotate( i * 360 / num, [0,0,1])	
					color(stone) wedge5(turret_radius+block_thickness,block_thickness,360/num,block_height, master_seed+i);
				}
			//The mortar
			if(mortar_thickness>.01){
				translate([0,0,-1*block_height])	
					scale([1,1,1/(height*z_spacing)])
						color(grout) mortar(turret_radius+block_thickness,mortar_thickness);
				}
			//The crenelations
			for(i=[1:num/2]){ 
				//Crenelations
				translate([0,0,2*block_height])	
					rotate( phase+i * 720 / num, [0,0,1])	
						color(stone) wedge5(turret_radius+block_thickness,block_thickness,(360*factor)/num,block_height,master_seed+num+i);
				}
			}
		}
	if(noob=="yes"){
		translate([2*rad+4*block_thickness,0,1*block_height]) union(){
			//The middle stones
			for(i=[1:num]){
				rotate( i * 360 / num, [0,0,1])	
					color(stone) wedge5(turret_radius+block_thickness,block_thickness,360/num,block_height, master_seed+i);
				}
			//The mortar
			translate([0,0,-1*block_height])	
				scale([1,1,1/(height*z_spacing)])
					color(grout) mortar(turret_radius+block_thickness,mortar_thickness);
			//The crenelations
			for(i=[1:num/2]){ 
				//Crenelations
				translate([0,0,2*block_height])	
					rotate( phase+i * 720 / num, [0,0,1])	
						color(stone) wedge5(turret_radius+block_thickness,block_thickness,(360*factor)/num,block_height,master_seed+num+i);
				}
			}
		//The conical base
		translate([0,2*rad+4*block_thickness,0])
			color(stone) cylinder(2*block_height,turret_radius+2*block_thickness,turret_radius+block_thickness);
		}
	}

module base(){
	for(h=[0:height-1]){
		rotate([0,0,90*(pow(-1,h))/num]) 
			translate([0,0,(h+.5)*block_height*2*z_spacing]) 
				union(){
					for(i=[1:num]){
					   rotate( i * 360 / num, [0,0,1])	
							wedge5(turret_radius,block_thickness,360*theta_expansion/num,block_height,master_seed+i+num*h);
						}
					}
		}
	}

module mortar(radius,thickness){
	//Makes a hollow cylinder in the middle of the bricks of the 
	inner_radius=radius+(1-thickness)*block_thickness/2;
	outer_radius=thickness*block_thickness;
	//translate([0,0,-block_height])
	linear_extrude(height=2*height*block_height*(z_spacing)-height*(z_spacing-1)){
		difference(){
			circle(inner_radius+outer_radius);
			circle(inner_radius);
			}
		}
	}

module wedge5(inner,width,theta,thickness,seed){
	//inner		=inner radius of arch/circle
	//width		=radial distance of block
	//theta		=angle subtended by block
	//thickness	=height of block
	random=rands(-1,1,n*3,seed);
	intersection(){
		wedge_boundary(inner,width,theta,thickness);
		correct(inner, width)	translate([inner+width/2,0,0])
			intersection_for(i=[0:n-1]){
				rotate([	max_angle*random[3*i]*pow(i*(thickness/inner),power),
							.7*max_angle*random[3*i+1]*pow(i,power),
							max_angle*random[3*i+2]*pow(i*(inner/width),power)])
					cube([width, sqrt((4*inner*tan(theta/2))*(width)), sqrt((4*inner*tan(theta/2))*(thickness))], center=true);
				}
		}	
	}

module correct(inner, width){
	//mirrors an object about its yz plane, which necessarily must be done is this ugly way
	translate([inner+width/2,0,0])
		mirror([1,0,0])
			translate([-inner-width/2,0,0])
				child(0);
	}

module wedge_boundary(inner,width,theta,thickness){
	//Creates a pie slice of theta degrees that has a radius of inner+width. Used to make sure that the wedge does not over-extend the angle it is supposed to.
	intersection(){
		rotate([0,0,-theta/2]) 
			translate([(inner+width)/2,(inner+width)/2,0])
				cube([inner+width,inner+width,2*thickness],center=true);
		rotate([0,0,theta/2]) 
			translate([(inner+width)/2,-(inner+width)/2,0])
				cube([inner+width,inner+width,2*thickness],center=true);
		}
	}