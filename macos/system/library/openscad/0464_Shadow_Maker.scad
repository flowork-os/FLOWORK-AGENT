// [FL_INDEX: keywords="openscad, 3d_parametric, Shadow_Maker, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Shadow Maker

// ===== file: ShadowMaker_v2.scad =====
//------------------------------------------------------------
//	Stencil-o-Matic
//
//	input comes from:
//	http://chaaawa.com/stencil_factory/
//
//	http://thingiverse.com/Benjamin
//	http://www.thingiverse.com/thing:55821
//------------------------------------------------------------

// preview[view:south, tilt:top]

light_height = 50;
projection_width=75;
enclosure_scale = 110; //[105:150]
thickness=1;
enclosure_type=0; //[0:Sphere,1:Diamond,2:Cylinder]
base_offset=10;
use_bounding_box=0; //[1:Yes,0:No]
bounding_box_width=200; //Input the size box you want the light to be limited by

// If you don't want to center
offX = 0;
offY = -60;

// paste here after "Convert&Copy"
input = "no_input";

module void() {}

vessel_scale=enclosure_scale/100;

points_array = (input=="no_input"? [[155,155],[[191,71.29],[185.87,71.67],[179.87,72.89],[173.25,75.07],[166.64,77.79],[160.58,80.93],[155.27,84.15],[150.61,87.65],[146.12,91.47],[141.78,95.93],[137.5,101],[133.43,107.05],[129.57,113.86],[126.38,121.28],[123.93,128.77],[122.45,137.29],[122,148],[122.46,158.81],[123.99,167.59],[126.57,175.53],[129.95,183.5],[134.22,190.97],[138.95,197.7],[144.17,203.41],[149.6,208.45],[155.36,212.68],[161.35,216.44],[167.93,219.61],[175.11,222.41],[182.22,224.29],[188.61,225.23],[194.5,225.5],[194.5,220.08],[194.5,214.67],[187.5,213.26],[180.5,211.4],[173.5,208.92],[166.62,205.39],[159.89,201.02],[154.13,196.18],[149.55,191.5],[145.9,186.6],[142.37,181.22],[139.18,174.83],[136.32,167.5],[134.22,159.01],[133.68,149],[134.08,139.49],[135.4,132],[137.87,125.06],[141.32,117.52],[146.29,109.61],[153.15,101.85],[161.16,94.8],[170.16,89.61],[178.7,86.02],[186,83.92],[191.03,82.9],[194,82.03],[195.13,80.27],[195.5,76.39],[195.5,71.5],[191,71.29]],[[208.65,71],[206.58,71.41],[205.41,72.39],[205.12,74.62],[205.19,78.06],[205.5,82.34],[212.5,83.69],[220.17,85.97],[228.84,89.61],[237.84,94.79],[245.85,101.85],[252.71,109.61],[257.68,117.52],[261.13,125.06],[263.6,132],[264.92,139.49],[265.32,149],[264.78,159.01],[262.67,167.5],[259.71,175.04],[256.28,181.93],[251.67,188.4],[245.91,194.93],[239.62,200.55],[233.75,204.82],[227.76,207.88],[221.21,210.56],[214.72,212.49],[208.88,213.75],[203.5,214.52],[203.19,218.83],[203.33,222.34],[204.14,224.66],[206.28,225.73],[210.95,225.51],[217.07,224.3],[224,222.35],[231.1,219.59],[237.65,216.44],[243.64,212.68],[249.4,208.45],[254.83,203.41],[260.05,197.7],[264.78,190.97],[269.05,183.5],[272.43,175.53],[275.01,167.59],[276.54,158.81],[277,148],[276.55,137.29],[275.07,128.77],[272.62,121.28],[269.43,113.86],[265.57,107.05],[261.5,101],[257.22,95.93],[252.88,91.47],[248.37,87.64],[243.67,84.12],[238.16,80.81],[231.67,77.52],[224.68,74.72],[217.94,72.62],[212.5,71.48],[208.65,71]],[[199,97.05],[179.07,97.38],[170.64,98.46],[167.02,100.27],[163.76,102.67],[161.09,105.84],[158.9,109.5],[157.04,113.5],[157.02,151.03],[157.28,181.92],[158.46,190.64],[160.4,192.49],[163.01,194],[166.28,194.78],[170.04,194.11],[173.18,192.62],[175.23,190.71],[176.33,181.01],[177,153],[177.5,117.5],[183.5,117.5],[189.5,117.5],[190,153.6],[190.67,182.22],[191.78,191.24],[193.56,192.69],[196.01,194.01],[198.8,194.69],[201.35,194.63],[203.74,193.64],[206.12,192.1],[208.5,190.18],[209,153.84],[209.5,117.5],[215.5,117.5],[221.5,117.5],[222,153],[222.67,181.01],[223.77,190.71],[225.82,192.62],[228.96,194.11],[232.72,194.78],[235.99,194],[238.6,192.49],[240.54,190.64],[241.72,181.92],[241.98,151.03],[241.96,113.5],[240.14,109.49],[237.78,105.72],[234.68,102.3],[231.01,99.74],[227.28,98.06],[217.63,97.32],[199,97.05]]]: input);

rL=(light_height+base_offset)/2;


intersection(){
	difference(){
		vessel(
			enclosure_type=enclosure_type,
			light_height = light_height,
			thickness=thickness,
			base_offset=base_offset,
			vessel_scale=vessel_scale);
		image_projection(points_array=points_array,
			projection_width=projection_width,
			light_height=light_height,
			offX=offX,
			offY=offY);
	}

	bounding_box(bbwidth=bounding_box_width,light_height=light_height);


}

%image_projection(points_array=points_array,
		projection_width=projection_width,
		light_height=light_height,
		offX=offX,
		offY=offY);

module image_projection(
	points_array,
	projection_width=150,
	light_height=50,
	offX=0,
	offY=0){
	
	dispo_width = projection_width;
	input_width = points_array[0][0];
	input_height= points_array[0][1];
	sTrace = dispo_width/input_width;
	stencil_height = input_height*sTrace;	

	light = [200-offX/sTrace,150+offY/sTrace,light_height];

	
	//translate([offX, offY, 0])
		scale([sTrace, -sTrace, 1])
		//translate([-200, -150, 0])
		for( i = [1:len(points_array)-1])union(){
			linear_extrude(height=light_height,scale=.01)
				translate([-200+offX/sTrace, -150-offY/sTrace, 0])
				polygon(points_array[i]);
//			translate([0,0,-.1])linear_extrude(height=.1)polygon(points_array[i]);
//			for( j = [0:len(points_array[i])-1]){
//						polyhedron(
//							points=[points_array[i][j],points_array[i][j+1],light],
//							triangles=[[0,1,2]]);
//						echo(points_array[i][j],points_array[i][j+1],light);
//			}
		}

}

//[0:Sphere,1:Diamond,2:Cylinder]
module vessel(
	enclosure_type=0,
	light_height = 50,
	thickness=1,
	base_offset=10,
	vessel_scale=1.1){

	d0=(light_height+base_offset)/pow(3,.5);
//	d1=d0*pow(2,.5)*sin(60)-d0*.5*pow(2,.5)*tan(30);
//	d2=pow(d0*d0-d1*d1,.5);

	if(enclosure_type==0)difference(){  //Sphere
		translate([0,0,rL*vessel_scale-base_offset])sphere(r=rL*vessel_scale);
		translate([0,0,-rL])cube(rL*2,center=true);
		difference(){
			translate([0,0,rL*vessel_scale-base_offset])sphere(r=rL*vessel_scale-thickness);	
			translate([0,0,-rL+thickness])cube(rL*2,center=true);
		}
		//translate([0,0,light_height/2])cylinder(r=rL/3,h=light_height,$fn=30);
	}

	if(enclosure_type==1)rotate([0,0,30])difference(){  //Diamond
		translate([0,0,-base_offset])
			rotate([0,-asin(1/pow(3,.5)),0])
			rotate([45,0,0])
			cube(d0*vessel_scale);
		difference(){
			translate([0,0,-base_offset+thickness*pow(3,.5)])
				rotate([0,-asin(1/pow(3,.5)),0])
				rotate([45,0,0])
				cube(d0*vessel_scale-2*thickness);
			translate([0,0,-rL+thickness])cube(rL*2,center=true);
		}
	}

	if(enclosure_type==2)difference(){  //Cylinder
		cylinder(r=light_height*vessel_scale/(1.618*2),h=light_height*vessel_scale,$fn=30);
		translate([0,0,thickness])cylinder(r=light_height*vessel_scale/(1.618*2)-thickness,h=light_height*vessel_scale-2*thickness,$fn=30);
		//translate([0,0,light_height/2])cylinder(r=rL/3,h=light_height,$fn=30);

	}

}

module bounding_box(bbwidth,light_height){
	if(use_bounding_box==1)linear_extrude(height=light_height,scale=.001)square(bbwidth,center=true);
	if(use_bounding_box!=1||enclosure_type==1)linear_extrude(height=light_height)circle(r=bbwidth,center=true,$fn=30);
}





