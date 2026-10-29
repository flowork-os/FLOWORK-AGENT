// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_starry__curvy__bowl__cup_or_vase, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable starry, curvy, bowl, cup or vase

//---------------------------------
// Author:  		Monique de Wilt
// Date:    		1-23 february 2013
// Description: 	this is a customizable design to make your own bowl, cup, vase, star, ring, candleholder or cookycutter. 
// 					The bottom and top diameters determine the depth and height sizes, with the oval you can make the width bigger or smaller 
//----------------------------------

// preview[view:north east, tilt:top diagonal]

//---[ USER definable Parameters ]-------------------------------

// in mm
Bottom_Plane_Diameter = 150; 	// 0:1000

// in mm
Top_Plane_Diameter =180; 		// 0:1000

//in mm
Height = 30; 	//0:1000

//less points for stars, more points for circles. It is now
Points =25; 				//[3:60]

// in %. 0 for no groove, bigger for sharper points. It is now                  
Groove_Depth=15; 		//[0:99]

// in %. 0 for a straight wall, - for a thinner middle, + for thicker
Curve = 20; 				//-100:5000

//in %, scales x dimension, Choose 100 for a circular thing. It is now
Oval = 100; 				//[1:500]

//in mm.  You will get uneven wall thickness when also using Oval.
Wall_Thickness = 14;	//0.3:1000

//in mm. Set this to bigger than the Height to get a solid
Bottom_Thickness =3;   //0.3:Height+10

//in mm. choose 0 if you do not want a round hole. Use the Bottom thickness for the depth.
Round_Hole_Diameter = 0;	//0:1000

//to check the inside. Set to "No" before creating your stl
Show_Crossection = 2; // [0:Yes,2:No,]

//Thanks to Build Plate Library for Customizer http://www.thingiverse.com/thing:44094 for buildplate selector

// for display only, doesn't contribute to final object
build_plate_selector = 3; //[0:Replicator 2,1: Replicator,2:Thingomatic,3:Manual, 4:No Buildplate]

// When Build Plate Selector is set to "manual" this controls the build plate x dimension
build_plate_manual_x = 200; //100:400

// When Build Plate Selector is set to "manual" this controls the build plate y dimension
build_plate_manual_y = 200; //100:400

// when Build Plate Selector is set to "manual" this controls the build volume z dimension
build_plate_manual_z = 150; //100:400

//---[ Automatically Calculated Parameters  ]-----------------

	Bottom_Radius = Bottom_Plane_Diameter / 2;
	Top_Radius = Top_Plane_Diameter / 2;
	Segment_Angle = 180 / Points;
	Half_Point_Angle =0.01 * (100-Groove_Depth) * ( 90 - Segment_Angle );
	Projected_Overhang= (Top_Radius - Bottom_Radius) * sin (Half_Point_Angle);
	Wall_Length = pow(((pow(Projected_Overhang,2)) + ( pow ( Height ,2))),0.5);
	Taille = Curve/(abs (Curve));  																				// gives +1 for thicker in the middle , -1 for Taille / thinner in the midddle
	Deviation_From_Straight_Wall = abs(Curve) * Wall_Length / 200 ;
	Max_Width = max(Bottom_Radius , Top_Radius) + (Deviation_From_Straight_Wall/sin (Half_Point_Angle))  ;
	Pizza_Width = Max_Width * (tan( Segment_Angle ));
	Half_Curve_Length=pow(((pow(( Wall_Length * 0.5),2)) + ( pow( Deviation_From_Straight_Wall ,2))),0.5);
	Quarter_Curve_Angle= atan( Deviation_From_Straight_Wall / ( Wall_Length * 0.5));
	Real_Curve_Radius = ( Half_Curve_Length * 0.5)/(cos (90 - Quarter_Curve_Angle ));
	Projected_Radius = (Real_Curve_Radius - Deviation_From_Straight_Wall ) / Wall_Length * Height ;
	Z_Curve_Center =(0.5 * Height )  + (( Real_Curve_Radius - Deviation_From_Straight_Wall ) / Wall_Length * ( (Top_Radius-Bottom_Radius) * sin(Half_Point_Angle)));
	Curve_Bottom_Angle = atan(Z_Curve_Center /( Projected_Radius - 0.5* Projected_Overhang));
	Inside_Radius = Real_Curve_Radius - ( Taille * Wall_Thickness );
	Inside_Radius_Bottom = pow((pow( Inside_Radius,2)) - ( pow( Z_Curve_Center - ((0.5 +( 0.5 *Taille))*Bottom_Thickness) ,2)),0.5);
	Inside_Radius_Top = pow((pow( Inside_Radius,2)) - ( pow( Z_Curve_Center - Height + ((0.5 -(0.5 *Taille))*Bottom_Thickness),2)),0.5);
	Inside_Curve_Bottom_Angle = acos(-max(-1,(-Z_Curve_Center + ((0.5 +( 0.5 *Taille))*Bottom_Thickness))/Inside_Radius))  ;//* (Z_Curve_Center - Bottom_Thickness/ abs(Z_Curve_Center-Bottom_Thickness))
	Inside_Curve_Top_Angle = acos(-min(1,(-Z_Curve_Center + Height - (0.5 -(0.5 *Taille))*Bottom_Thickness)/Inside_Radius))  ; //* (Z_Curve_Center-Height/ abs(Z_Curve_Center-Height))
	Quarter_Inside_Curve_Angle = 0.25 *(Inside_Curve_Top_Angle - Inside_Curve_Bottom_Angle);
	
//---[ Coordinates for Cross Sections ]--------

	//--Corner Points--------------------------------------------------
	pxa = Projected_Radius - Taille*0.5 * Projected_Overhang - Taille * Bottom_Radius ;	
	pxb = pxa ;	
	pxc = Projected_Radius - 0.5 * Projected_Overhang ;
	pxd = Projected_Radius + 0.5 * Projected_Overhang ; 
	pxe = Projected_Radius + 0.5 * Projected_Overhang - Wall_Thickness ;
	pxj = Inside_Radius_Bottom ;
	pxk = Inside_Radius_Top ; 
	pxm = pxa ;	
	pxf = pxe ;
	
	pxaa  = Projected_Radius - 0.5 * Projected_Overhang + Bottom_Radius ;
	pxmm = pxaa ;	

	pya = -	Z_Curve_Center + Bottom_Thickness ;
	pyb = -	Z_Curve_Center ;
	pyc = -	Z_Curve_Center ;
	pyd = - Z_Curve_Center + Height ;
	pye = -	Z_Curve_Center + Height ;
	pyj = -	Z_Curve_Center + ((0.5 +( 0.5 *Taille))* Bottom_Thickness) ;
	pyk = - Z_Curve_Center + Height ;
	pym = - Z_Curve_Center + Height ;
	pyf = pow((pow( Inside_Radius,2)) - ( pow( pxe ,2)),0.5);
	
	//--Outside Curve Points----------------------------------------------------------
	
	corr= 90 *(pxc/abs(pxc));  //=+90 or -90, takes care of correct + or - .This will go wrong if pxc=0 but I couldn't find another away to do it

	px0 =  sin( Curve_Bottom_Angle  + corr )*  Real_Curve_Radius  ; 
	px1 =  sin(-0.2 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	px2 =  sin(-0.4 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	px3 =  sin(-0.6 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px4 =  sin(-0.8 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px5 =  sin(-1 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px6 =  sin(-1.2 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px7 =  sin(-1.4 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px8 =  sin(-1.6 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px9 =  sin(-1.8 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px10 = sin(-2 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px11 =  sin(-2.2 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px12 =  sin(-2.4 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px13 =  sin(- 2.6 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px14 =  sin(- 2.8 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px15 =  sin(- 3 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px16 =  sin(- 3.2 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px17 =  sin(- 3.4 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px18 =  sin(- 3.6 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px19 =  sin(- 3.8 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	px20 =  sin(- 4 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ;  
	
	
	py0 = cos( Curve_Bottom_Angle  + corr )*  Real_Curve_Radius ; 
	py1 = cos( -0.2 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py2 = cos( -0.4 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py3 = cos( -0.6 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py4 = cos( -0.8 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py5 = cos( -1 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py6 = cos( -1.2 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py7 = cos( -1.4 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py8 = cos( -1.6 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py9 = cos( -1.8 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py10 = cos( -2 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py11 = cos( -2.2 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py12 = cos( -2.4 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py13 = cos( -2.6 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py14 = cos( -2.8 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py15 = cos( -3 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py16 = cos( -3.2 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py17 = cos( -3.4 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py18 = cos( -3.6 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py19 = cos( -3.8 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 
	py20 = cos( -4 * Quarter_Curve_Angle + Curve_Bottom_Angle + corr )*  Real_Curve_Radius ; 

	
	//--Inside Curve Points-------------------------------------------------------------------------
	px101 =abs( sin( 0.5 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius );
	px102 =abs( sin( 1 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius );
	px103 =abs( sin( 1.5 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius );
    px104 =abs( sin( 2 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius );
	px105 =abs( sin( 2.5 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius );
	px106 =abs( sin( 3 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius );
	px107 =abs( sin( 3.5 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius );
    px108 =abs( sin( 4.0 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius );

	py101 =-( cos( 0.5 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius) ; 
	py102 =-( cos( 1 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius) ; 
	py103 =-( cos( 1.5 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius) ; 
	py104 =-( cos( 2 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius) ; 
	py105 =-( cos( 2.5 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius) ; 
	py106 =-( cos( 3 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius) ; 
	py107 =-( cos( 3.5 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius) ; 
	py108 =-( cos( 4.0 * Quarter_Inside_Curve_Angle + Inside_Curve_Bottom_Angle)* Inside_Radius) ; 
	

//---[ M O D U L E S ]--------------------------------------------------------

	
	module SolidSection()										// Cross section of Outside Shape with Curve
	{
		polygon([
				[pxb, pyb],
				//[pxc, pyc],
				[px0, py0],
				 [px1, py1],
				 [px2, py2],
				 [px3, py3],
				 [px4, py4],
				 [px5, py5],
				[px6, py6],
				 [px7, py7],
			     [px8, py8],
				  [px9, py9],
				 [px10, py10], 
				 [px11, py11],
				 [px12, py12],
				 [px13, py13],
				 [px14, py14],
				[px15, py15],
				 [px16, py16],
				[px17, py17],
			    [px18, py18],
			    [px19, py19],
			   [px20, py20],
				//[pxd, pyd],
				[pxm, pym]
				],[]);					
	}	
	

	module BottomVoid(topinsideradius, bottominsideradius)			//Hole formed by bottom Thickness
	{
		polygon([
				[pxa-10, pya],
				[bottominsideradius, pyj],
				[topinsideradius, pyk],
				[pxm-1, pym+1],
				],[]);
	}

	module BVoid()													// changes B Void shape when inside ball doesn't cross bottom or top plane
	{
		if (  Z_Curve_Center - Bottom_Thickness >Inside_Radius)  
		{
			if ( (- Z_Curve_Center + Height)>Inside_Radius)    		//when inside ball doesn't cross bottom and doesn't cross top
			{ 
					BottomVoid(pxe, 0);
			}else{                                            
				if ( pxe-pxk > Wall_Thickness)   				//when inside ball doesn't cross bottom but does cross top and would leave a very sharp edge at the top 
				{ 	
					BottomVoid(pxe, 0);
				}else{											//when inside ball doesn't cross bottom but does cross top with edge that is not that sharp
					BottomVoid(pxk, 0);
				}
			}
		}else{	
			if ( (- Z_Curve_Center + Height)>Inside_Radius)		//when inside ball does cross bottom but doesn't cross top
			{ 
					BottomVoid(pxe, pxj);
			}else{
				if ( pxe-pxk > Wall_Thickness)					//when inside ball does cross bottom and does cross top and would leave a very sharp edge at the top 
				{ 	
					BottomVoid(pxe, pxj);
				}else{											//when inside ball does cross bottom and does cross top with edge that is not that sharp
					BottomVoid(pxk, pxj);
				}
			}
		}	
	}	
   
	module InsideRadiusVoid(topinsideradius, bottominsideradius, topcut)    //Hole formed by Wall Thickness
	{ 
		polygon([
					[pxa - (Taille *11), ((0.5 +( 0.5 *Taille))*pya) + ((0.5 -( 0.5 *Taille))*pyb)],
					[bottominsideradius,pyj],
					[px101, py101],
					[px102, py102],
					[px103, py103],
					[px104, py104],
					[px105, py105],
					[px106, py106],
					[px107, py107],
					[topinsideradius, topcut],
					[pxa - (Taille *11),topcut]
				],[]);
	}

	module IRVoid()													//  Changes IRVoid shape when inside "ball" doesn't cross bottom or top plane
	{
		if (  Z_Curve_Center - Bottom_Thickness >Inside_Radius)		
		{
			if ( (- Z_Curve_Center + Height)>Inside_Radius)			//when inside ball doesn't cross bottom and doesn't cross top
			{ 
					InsideRadiusVoid(pxa-2, 0,pyf);
			}else{
				if ( pxe-pxk > Wall_Thickness)						//when inside ball doesn't cross bottom but does cross top and would leave a very sharp edge at the top 
				{ 	
					InsideRadiusVoid(pxa-2, 0,pyf);
				}else{												//when inside ball doesn't cross bottom but does cross top with edge that is not that sharp
					InsideRadiusVoid(pxk, 0,py108);
				}
			}
		}else{	
			if ( (- Z_Curve_Center + Height)>Inside_Radius)			//when inside ball does cross bottom but doesn't cross top
			{ 
					InsideRadiusVoid(pxa-2, pxj, Inside_Radius);   
			}else{													
				if ( pxe-pxk > Wall_Thickness)						//when inside ball does cross bottom and does cross top and would leave a very sharp edge at the top 
				{ 	
					InsideRadiusVoid(pxk, pxj, pyf);
				}else{												//when inside ball does cross bottom and does cross top with edge that is not that sharp
					InsideRadiusVoid(pxk, pxj, py108);
				}
			}
		}	
	}	
	
	 
	module Section()									//Decides Which crossections are used              
	{
		if(Round_Hole_Diameter > 0)						// no starry hole, only a round hole which is in module HoleCutter
		{
			SolidSection();
		}else{	
			if (Bottom_Thickness < Height)
			{
				if (Curve < 0)
				{
					difference()							//starry hole with curvy walls
								{
									SolidSection();
									IRVoid();
								}
				}else{
							if (Inside_Radius > 0)
							{
								difference()							//starry hole with curvy walls
								{
									 //translate ([ 0, 0 , 10])		// makes debugging easier
									 SolidSection();
									 // translate ([ 0, 0 , 5])		// makes debugging easier
									 BVoid();
									 IRVoid();
								}
							}else{
								difference()							//only a starry hole shaped by bottom thickness, straight walls
								{
									SolidSection();
									BVoid();
								}
							}
				}
			}else{													//No holes
			 SolidSection();
			}
		}
	}
	
	module Walls() 										// positions curved Walls 
	{
		translate ([((Bottom_Radius + Top_Radius)/2 ),0,(0.5 - (0.5 * Taille ))*Height])		
			rotate ([0,0,90-Half_Point_Angle])
			rotate ([0,90-(Taille*90),0])										 
				translate ([-Projected_Radius, 0 , 0 ])
					translate ([ 0, Max_Width  , Z_Curve_Center])
						rotate([ 90 , 0 , 0 ])														
						{
							linear_extrude(height = 2* Max_Width)
							     Section();
						}	
	}
	
	module StraightSection()								// makes and positions straight walls
	{
		
		translate ([Bottom_Radius, 0 , 0 ])
		rotate ([0,0,90-Half_Point_Angle])
		translate ([-Bottom_Radius, 0 , 0 ])
		rotate([ 90 , 0 , 0 ])	
		linear_extrude(height = 2* Max_Width, center = true)		
		polygon([
				[0, 0],
				[Bottom_Radius, 0],
				[Bottom_Radius + Projected_Overhang, Height],
				[Bottom_Radius + Projected_Overhang-(( Wall_Length / Height )*Wall_Thickness), Height],  //wall thickness nog loodrecht op wand meten
				[Bottom_Radius -(( Wall_Length / Height )*Wall_Thickness) + ((Bottom_Thickness/Height)*Projected_Overhang), Bottom_Thickness],    //wall thickness op juiste hoogte nog
				[0, Bottom_Thickness], 
				],[]);
	}
	
	
	module CurvesOrStraight()
	{
		if(Curve > 0)						
		{							
			 Walls();
		}else{
				if(Curve < 0)						
					{							
						Walls();
					}else{		
						StraightSection();
					}
		}
	}	
	
	module Pizzacutter() 						
	{
		translate ([ 0, 0 , -Deviation_From_Straight_Wall])
			linear_extrude(height = Height + (2* Deviation_From_Straight_Wall))
				polygon([[0,0],[Max_Width , Pizza_Width + 0.05 ],[ Max_Width ,0 ]],[]);
	}

	module Assemble()				
	{
		union()
		{
			mirror ([ 0, 1, 0 ]) 
			{
				 intersection () 
				 {
					  Pizzacutter();
					  CurvesOrStraight();
				 }
			}
			intersection () 
				{
				 Pizzacutter();
				 CurvesOrStraight();
				}
		}
	}

	module Pattern()
	{
		union()  
		{
			for ( i = [0 : Points-1] )
				{
				rotate ( i * 360/ Points, [0,0,1])
					          Assemble();
				}
		}
	}
	
	module Oval()
	{
	scale (v= [0.01* Oval,1,1])
		{
		  Pattern();
		}
	}
	
	module HoleCutter()								// adds round hole 
	{
		if(Round_Hole_Diameter > 0)						
		{
			difference()							
			{
				Oval();
				translate ([ 0, 0 , Bottom_Thickness])
				cylinder(h=Height, r=0.5*Round_Hole_Diameter);
			}
		}else{	
			Oval();
		}
	}	
	
	module ShowSection()
	{	
		if (Show_Crossection <1)
		{
			difference()
			{
				HoleCutter();
				translate ([1.5 * Max_Width, 0 , 0.6 * Height])
				cube(size =[3*Max_Width,2*Max_Width,Height*1.25],center = true);
			}
		}else{
			HoleCutter();
		}
	}
	ShowSection();
	
	module build_plate(bp,manX,manY,manZ)
	{

		translate([0,0,-.52])
		{
			if(bp == 0){
				%cube([285,153,1],center = true);
				translate([0,-76.5 ,77.5 + 0.52])
				rotate ([90,0,0])
				%cube([285,155,1],center = true);
			}
			if(bp == 1){
				%cube([225,145,1],center = true);
				translate([0,-72.5 ,75 + 0.52])
				rotate ([90,0,0])
				%cube([225,150,1],center = true);
			}
			if(bp == 2){
				%cube([120,120,1],center = true);
				translate([0,-60 ,60 + 0.52])
				rotate ([90,0,0])
				%cube([120,120,1],center = true);
			}
			if(bp == 3){
				%cube([manX,manY,1],center = true);
				translate([0,-0.5*manY ,0.5 * manZ + 0.52])
				rotate ([90,0,0])
				%cube([manX,manZ,1],center = true);
			}
		
		}
		translate([0,0,-.5])
		{
			if(bp == 0){
				for(i = [-14:14]){
					translate([i*10,0,0])
					%cube([0.5,153,1.01],center = true);
				}
				for(i = [-7:7]){
					translate([0,i*10,0])
					%cube([285,0.5,1.01],center = true);
				}
				translate([0,-76.5 ,77.5 + 0.52])
					rotate ([90,0,0])				
					for(i = [-14:14]){
						translate([i*10,0,0])
						%cube([0.5,153,1.01],center = true);
					}
				translate([0,-76.5 ,77.5 + 0.52])
					rotate ([90,0,0])
					for(i = [-7:7]){
						translate([0,i*10,0])
						%cube([285,0.5,1.01],center = true);
					}	
			}
			if(bp == 1){
				for(i = [-11:11]){
					translate([i*10,0,0])
						%cube([0.5,145,1.01],center = true);
				}
				for(i = [-7:7]){
					translate([0,i*10,0])
						%cube([225,0.5,1.01],center = true);
				}
				translate([0,-72.5 ,75 + 0.52])
				rotate ([90,0,0])
				for(i = [-11:11]){
					translate([i*10,0,0])
						%cube([0.5,145,1.01],center = true);
				}
				translate([0,-72.5 ,75 + 0.52])
				rotate ([90,0,0])
				for(i = [-7:7]){
					translate([0,i*10,0])
						%cube([225,0.5,1.01],center = true);
				}
			}
			if(bp == 2){
				for(i = [-6:6]){
					translate([i*10,0,0])
						%cube([0.5,120,1.01],center = true);
				}
				for(i = [-6:6]){
					translate([0,i*10,0])
						%cube([120,0.5,1.01],center = true);
				}
				translate([0,-60 ,60 + 0.5])
				rotate ([90,0,0])
				for(i = [-6:6]){
					translate([i*10,0,0])
						%cube([0.5,120,1.01],center = true);
				}
				translate([0,-60 ,60 + 0.5])
				rotate ([90,0,0])
				for(i = [-6:6]){
					translate([0,i*10,0])
						%cube([120,0.5,1.01],center = true);
				}
			}
			if(bp == 3){
				for(i = [-(floor(manX/20)):floor(manX/20)]){
					translate([i*10,0,0])
						%cube([0.5,manY,1.01],center = true);
				}
				for(i = [-(floor(manY/20)):floor(manY/20)]){
					translate([0,i*10,0])
						%cube([manX,0.5,1.01],center = true);
				}
				translate([0,-0.5*manY ,0.5 * manZ + 0.5])
				rotate ([90,0,0])
				for(i = [-(floor(manX/20)):floor(manX/20)]){
					translate([i*10,0,0])
						%cube([0.5,manZ,1.01],center = true);
				}
				translate([0,-0.5*manY ,0.5 * manZ + 0.5])
				rotate ([90,0,0])
				for(i = [-(floor(manZ/20)):floor(manZ/20)]){
					translate([0,i*10,0])
						%cube([manX,0.5,1.01],center = true);
				}
			}
		}
	}


if( build_plate_selector <4)
{
build_plate(build_plate_selector,build_plate_manual_x,build_plate_manual_y,build_plate_manual_z);
}
	
	//Check sizes:
	//cylinder(h=Height-1,r1=Bottom_Radius-1, r2=Top_Radius , center = false);