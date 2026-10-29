// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_laser_cutted_box, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable laser cutted box


//Customizable Box 
//By Iron Momo


/* [Basic] */
box_width = 250;
box_height = 200;
box_depth = 100;
material_thickness = 5; //[3,5,10]

output_type = "STL"; //[DXF,STL]

/* [Advanced] */
spacing = 5; //[1,5,10]
ratio = 0.5; //[0.25,0.5]


/* [Hidden] */
h2 = box_height*ratio; //Height of the upper part
h1 = box_height*(1-ratio); //Height of the lower part

// preview[view: north, tilt:top]


if(output_type=="STL")
{linear_extrude(height = material_thickness, center = false) box_creation();
}

if(output_type=="DXF")
{box_creation();}



/*--------------*/
/* BOX CREATION */
/*--------------*/
module box_creation()
{
	top();
	translate([0,spacing+box_depth+2*material_thickness]) front_1();
	translate([0,2*spacing+box_depth+h1+3*material_thickness]) front_2();
	translate([0,3*spacing+4*material_thickness+box_depth+h1+h2,0]) bottom();
	translate([box_width+2*material_thickness+spacing,0,0])rear();
	translate([box_width+2*material_thickness+spacing,material_thickness+box_height+spacing,0]) sides();
}

/*----------------*/
/* Top of the box */
/*----------------*/
module top()
{

//Basic shape
translate([material_thickness,material_thickness,0]) square([box_width,box_depth]); 

//Notches
translate([0,material_thickness+box_depth,0]) square([box_width+2*material_thickness,material_thickness]);

translate([0,material_thickness,0]) square([material_thickness,box_depth/3]);
translate([0,material_thickness+2*box_depth/3,0]) square([material_thickness,box_depth/3]);

translate([material_thickness+box_width,material_thickness,0]) square([material_thickness,box_depth/3]);
translate([material_thickness+box_width,material_thickness+2*box_depth/3,0]) square([material_thickness,box_depth/3]);

translate([material_thickness+box_width/5,0,0]) square([box_width/5,material_thickness]);
translate([material_thickness+3*box_width/5,0,0]) square([box_width/5,material_thickness]);


}


/*--------------------*/
/* 2 sides of the box */
/*--------------------*/
module sides()
{
//1st side, upper and lower part
side_1();
translate ([material_thickness,h1+spacing+material_thickness,0]) side_2();

//2nd side is just a mirrored one
translate([2*box_depth+4*material_thickness+spacing,0,0])
{
	mirror ([1,0,0])
		{
		side_1();
		translate ([material_thickness,h1+spacing+material_thickness,0]) side_2();
		}
	}
}
/*------------------*/
/* Side: Upper part */
/*------------------*/
module side_2()
{

//Basic shape
polygon(points=[[0,h2],[box_depth,h2],[box_depth,0]], paths=[[0,1,2]]);

//Notches
translate([box_depth,h2/5,0]) square([material_thickness,h2/5]);
translate([box_depth,3*h2/5,0]) square([material_thickness,h2/5]);

translate([box_depth/3,h2,0]) square([box_depth/3,material_thickness]);
}

/*------------------*/
/* Side: Lower part */
/*------------------*/
module side_1()
{

//Basic shape
translate([material_thickness,material_thickness,0])
	{
	square([box_depth,h1]);
	polygon(points=[[0,box_height],[0,h1],[box_depth,h1]], paths=[[0,1,2]]);
	}

//Notches
translate([material_thickness+box_depth/3,0,0]) square([box_depth/3,material_thickness]);

translate([0,material_thickness+box_height/7,0]) square([material_thickness,box_height/7]);
translate([0,material_thickness+3*box_height/7,0]) square([material_thickness,box_height/7]);
translate([0,material_thickness+5*box_height/7,0]) square([material_thickness,box_height/7]);

translate([material_thickness+box_depth,material_thickness+h1/5,0]) square([material_thickness,h1/5]);
translate([material_thickness+box_depth,material_thickness+3*h1/5,0]) square([material_thickness,h1/5]);
}




/*-------------------------*/
/* Front plate: Upper part */
/*-------------------------*/
module front_2()
{

//Basic shape
translate([material_thickness,0,0]) square([box_width,h2]);

//Notches
translate([0,h2,0]) square([box_width/5+material_thickness,material_thickness]);
translate([material_thickness+2*box_width/5,h2,0]) square([box_width/5,material_thickness]);
translate([material_thickness+4*box_width/5,h2,0]) square([material_thickness+box_width/5,material_thickness]);

square([material_thickness,h2/5]);
translate([0,2*h2/5,0]) square([material_thickness,h2/5]);
translate([0,4*h2/5,0]) square([material_thickness,h2/5]);
	
translate([material_thickness+box_width,0,0]) square([material_thickness,h2/5]);
translate([material_thickness+box_width,2*h2/5,0]) square([material_thickness,h2/5]);
translate([material_thickness+box_width,4*h2/5,0]) square([material_thickness,h2/5]);
}


/*-------------------------*/
/* Front plate: Lower part */
/*-------------------------*/
module front_1()
{

//Basic shape
translate([material_thickness,material_thickness,0]) square([box_width,h1]);
	
//Notches
square([box_width/5+material_thickness,material_thickness]);
translate([material_thickness+2*box_width/5,0,0]) square([box_width/5,material_thickness]);
translate([material_thickness+4*box_width/5,0,0]) square([material_thickness+box_width/5,material_thickness]);

translate([0,material_thickness,0]) square([material_thickness,h1/5]);
translate([0,material_thickness+2*h1/5,0]) square([material_thickness,h1/5]);
translate([0,material_thickness+4*h1/5,0]) square([material_thickness,h1/5]);

translate([material_thickness+box_width,material_thickness,0]) square([material_thickness,h1/5]);
translate([material_thickness+box_width,material_thickness+2*h1/5,0]) square([material_thickness,h1/5]);
translate([material_thickness+box_width,material_thickness+4*h1/5,0]) square([material_thickness,h1/5]);
}


/*------------*/
/* Back plate */
/*------------*/
module rear()
{

//Basic shape
translate([material_thickness,material_thickness,0]) 
	{
	difference()
		{
		square([box_width,box_height]);
		translate([10,box_height-2,0]) square([box_width-20,2]);
		}
	}

square([box_width/5+material_thickness,material_thickness]);

//Notches
translate([material_thickness+2*box_width/5,0,0]) square([box_width/5,material_thickness]);
translate([material_thickness+4*box_width/5,0,0]) square([box_width/5+material_thickness,material_thickness]);
	
translate([0,material_thickness,0]) square([material_thickness,box_height/7]);
translate([0,material_thickness+2*box_height/7,0]) square([material_thickness,box_height/7]);
translate([0,material_thickness+4*box_height/7,0]) square([material_thickness,box_height/7]);
translate([0,material_thickness+6*box_height/7,0]) square([material_thickness,box_height/7]);

translate([material_thickness+box_width,material_thickness,0]) square([material_thickness,box_height/7]);
translate([material_thickness+box_width,material_thickness+2*box_height/7,0]) square([material_thickness,box_height/7]);
translate([material_thickness+box_width,material_thickness+4*box_height/7,0]) square([material_thickness,box_height/7]);
translate([material_thickness+box_width,material_thickness+6*box_height/7,0]) square([material_thickness,box_height/7]);
}

/*--------------*/
/* Bottom plate */
/*--------------*/
module bottom()
{

//Basic shape
translate([material_thickness,material_thickness,0]) square([box_width,box_depth]);

//Notches
translate([material_thickness+box_width/5,0,0]) square([box_width/5,material_thickness]);
translate([material_thickness+3*box_width/5,0,0]) square([box_width/5,material_thickness]);
translate([material_thickness+box_width/5,material_thickness+box_depth,0]) square([box_width/5,material_thickness]);
translate([material_thickness+3*box_width/5,material_thickness+box_depth,0]) square([box_width/5,material_thickness]);

translate([0,material_thickness,0]) square([material_thickness,box_depth/3]);
translate([0,material_thickness+2*box_depth/3,0]) square([material_thickness,box_depth/3]);
translate([material_thickness+box_width,material_thickness,0]) square([material_thickness,box_depth/3]);
translate([material_thickness+box_width,material_thickness+2*box_depth/3,0]) square([material_thickness,box_depth/3]);
}