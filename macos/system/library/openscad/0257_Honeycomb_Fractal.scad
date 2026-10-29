// [FL_INDEX: keywords="openscad, 3d_parametric, Honeycomb_Fractal, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Honeycomb Fractal

// The length of the side of the root hexagon.
sidelength = 20; // [1:100]
//The total height of the model.
height = 30; // [1:100]
//The cross-sectional wall thickness.
thickness = 1; // [1:20]
//The level of recursion depth
level = 2;	// [1,2,3,4]
//Should this be a tree, or constrained to a hexagonal shape?
tree_or_hex = "tree"; // [tree,hex]
//Should the model have a hexagon cone bottom?
bottom = "yes"; // [yes,no]

module hex(s, height){
	linear_extrude(height = height)polygon( points=[[s/2,sqrt(3)/2*s],[s,0],[s/2,-sqrt(3)/2*s],[-s/2,-sqrt(3)/2*s],[-s,0],[-s/2,sqrt(3)/2*s]] );
}
module hexcone(s, h){
	polyhedron(
  		points=[[s/2,sqrt(3)/2*s,h],[s,0,h],[s/2,-sqrt(3)/2*s,h],[-s/2,-sqrt(3)/2*s,h],[-s,0,h],[-s/2,sqrt(3)/2*s,h],[0,0,0]],
  		triangles=[[0,6,1],[1,6,2],[2,6,3],[3,6,4], [4,6,5], [5,6,0]  ,      // each triangle side
              			[0,1,2],[0,2,3],[0,3,4],[0,4,5] ]                         // four triangles for hex base
	);
}

module hexconehole(s,h,thickness,walls=true){
	hdiff = h/(s*sqrt(3)/2)*thickness;
	difference(){
		union(){
			hexcone(s,h);
			if(walls){
				rotate(30)translate([-thickness/2/sqrt(3),-thickness/2,0])cube([s*sqrt(3)/2+thickness/2/sqrt(3),thickness,h]);
				rotate(150)translate([-thickness/2/sqrt(3),-thickness/2,0])cube([s*sqrt(3)/2+thickness/2/sqrt(3),thickness,h]);
			}
		}
		translate([0,0,hdiff])hexcone(s,h);
	}
}

module hexconefractal(sidelen,height,width,walls=true,bottom=true){
	bs = sidelen-width/sqrt(3);
	smalllen = (bs+width)/sqrt(3);
	smallheight = height/2;
	smallwidth = width;
	for (i=hexpoints){
		translate([0,0,height*1/2])rotate(30)translate([i[0]*bs,i[1]*bs,i[2]*bs])rotate(i[3])hexconehole(smalllen,smallheight,width);
	}
	if (bottom){
		hexconehole(sidelen,height/2,width);
	}
}

module hexconefractal2(sidelen,height,width,walls=true,bottom=true){
	bs = sidelen-width/sqrt(3);
	smalllen = (bs+width)/sqrt(3);
	smallheight = height/2;
	smallwidth = width;
	for (i=hexpoints){
		translate([0,0,height*1/2])rotate(30)translate([i[0]*bs,i[1]*bs,i[2]*bs])rotate(i[3])hexconefractal(smalllen,smallheight,width);
	}
	if (bottom){
		hexconehole(sidelen,height/2,width,walls);
	}
}

module hexconefractal3(sidelen,height,width,walls=true,bottom=true){
	bs = sidelen-width/sqrt(3);
	smalllen = (bs+width)/sqrt(3);
	smallheight = height/2;
	smallwidth = width;
	for (i=hexpoints){
		translate([0,0,height*1/2])rotate(30)translate([i[0]*bs,i[1]*bs,i[2]*bs])rotate(i[3])hexconefractal2(smalllen,smallheight,width);
	}
	if (bottom){
		hexconehole(sidelen,height/2,width,walls);
	}
}

module hexconefractal4(sidelen,height,width,walls=true,bottom=true){
	bs = sidelen-width/sqrt(3);
	smalllen = (bs+width)/sqrt(3);
	smallheight = height/2;
	smallwidth = width;
	for (i=hexpoints){
		translate([0,0,height*1/2])rotate(30)translate([i[0]*bs,i[1]*bs,i[2]*bs])rotate(i[3])hexconefractal3(smalllen,smallheight,width);
	}
	if (bottom){
		hexconehole(sidelen,height/2,width,walls);
	}
}

module hexconefractaln(sidelen,height,width,n,tree,walls=true,bottom=true){
	//manually unrolling the recursion because openscad doesn't support recursion.
	if(n==1){
		hexconefractal(sidelen,height,width,walls,bottom);
	}else if (n==2){
		hexconefractal2(sidelen,height,width,walls,bottom);
	}else if (n==3){
		hexconefractal3(sidelen,height,width,walls,bottom);
	}else if (n==4){
		hexconefractal4(sidelen,height,width,walls,bottom);
	}else{
		hexconefractal(sidelen,height,width,walls,bottom);
	}
		

	
}

module parseoptions(sidelen,height,width,n,tree,bottom){
	intersection(){
		if (bottom== "yes"){
			
			translate([0,0,height])rotate(180,[0,1,0])hexconefractaln(sidelen,height,width,n,tree,walls=false,bottom=true);
		} else {
			translate([0,0,-height/2])hexconefractaln(sidelen,height,width,n,tree,walls=false,bottom=false);
		}
		if(tree == "hex")
			hex(sidelen,height);
		
	}
}
hexpoints = [[sqrt(3)/2,1/2,0,120],[0,1,0,180],[-sqrt(3)/2,1/2,0,-120],[-sqrt(3)/2, -1/2,0,-60],[0,-1,0,0],[sqrt(3)/2, -1/2,0,60]];
parseoptions(sidelength,height,thickness,level,tree_or_hex,bottom);