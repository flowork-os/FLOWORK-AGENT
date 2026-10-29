// [FL_INDEX: keywords="openscad, 3d_parametric, Bicycle_Light_Mount, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Bicycle Light Mount

/*******************************************************************
/  Bike Light Mount
/  Ryan Stachurski, 2012-05-28
/  --------------------------------------------
/  Mount to attach a flashlight to your handlebars.
/  Durable, and easy to aim and adjust.
/  Needs 6 skinny nuts and bolts, and one about 1/4" for the pivot. 
/  Adjust the values for your handlebars and flashlight ;)
/*******************************************************************/

// Layout Constant
PART_GAP = 0.25;

// Constants for Handlebar Clamps in inches
HANDLEBAR_TUBE_DIAMETER = 1.01 ;                          
HANDLEBAR_CLAMP_WIDTH = .3 ;
HANDLEBAR_CLAMP_THICKNESS = .2 ;
HANDLEBAR_CLAMP_BOLT_DIAMETER = 0.12 ;
HANDLEBAR_CLAMP_BOLT_CAP_DIAMETER = 0.22 ;

//derived
	HC_MAXX = HANDLEBAR_TUBE_DIAMETER/2 + HANDLEBAR_CLAMP_WIDTH; //note width is only used because of shared value
	HC_MAXY = HANDLEBAR_TUBE_DIAMETER/2 + HANDLEBAR_CLAMP_THICKNESS;
	HC_BOLTX = HC_MAXX - HANDLEBAR_CLAMP_WIDTH/2; //note width is only used because of shared value

//Constants for Handlebar Clamp Drops
HANDLEBAR_CLAMP_DROP_LENGTH = 2; 
HANDLEBAR_CLAMP_DROP_BOLT_DIAMETER = 0.25;

//Constants for light clamp  (bigger light d=1.51,  small light d=1.2)
LIGHT_DIAMETER = 1.2;
LIGHT_CLAMP_WIDTH = 2;
LIGHT_CLAMP_FLANGE = 0.3;
LIGHT_CLAMP_THICKNESS = .2;
LIGHT_CLAMP_BOLT_DIAMETER = 0.25;
LIGHT_CLAMP_BRACKETL_MIN = 1.5;		//Measure the bikes handlebar bracket width 
//derived
	LC_MAXX = LIGHT_DIAMETER/2 + LIGHT_CLAMP_FLANGE;
	LC_MAXY = LIGHT_DIAMETER/2 + LIGHT_CLAMP_THICKNESS;
	LC_BOLTX = LC_MAXX - LIGHT_CLAMP_FLANGE/2;
	SUPX = LC_MAXY-sqrt(pow(LC_MAXY,2)-pow(LIGHT_DIAMETER/2,2)); //Used to calculate where brace triangle meets cylinder 
	SUPY = (LIGHT_CLAMP_WIDTH-(LIGHT_CLAMP_THICKNESS*2+LIGHT_CLAMP_BOLT_DIAMETER))/2;
	BRACKETL = LIGHT_DIAMETER+(LIGHT_CLAMP_FLANGE-HANDLEBAR_CLAMP_BOLT_CAP_DIAMETER); //length of bracket: don't cover bolt
	BRACKETR = LIGHT_CLAMP_THICKNESS+LIGHT_CLAMP_BOLT_DIAMETER/2; //radius of bracket


module BoltCut () {
	union () {
		cylinder (h=HC_MAXY, r=HANDLEBAR_CLAMP_BOLT_CAP_DIAMETER/2, center=false); //bolt cap inset
		cylinder (h=HC_MAXY*2, r=HANDLEBAR_CLAMP_BOLT_DIAMETER/2, center=true); //bolt shaft
	}//end union
} //end BoltCut

module ClampBoltCut () {
	translate ([HC_BOLTX,-(HANDLEBAR_CLAMP_WIDTH-HANDLEBAR_CLAMP_BOLT_CAP_DIAMETER/2),0]) rotate ([90,0,0]) BoltCut ();
} //end ClampBoltCut

module LightClampBoltCut () {
	translate ([LC_BOLTX,-(LIGHT_CLAMP_FLANGE-HANDLEBAR_CLAMP_BOLT_CAP_DIAMETER/2),0]) rotate ([90,0,0]) BoltCut ();

} //end LightClampBoltCut

module HandlebarClamp () {
	difference () {
		//Start object

		union () {
		cylinder (h=HANDLEBAR_CLAMP_WIDTH, r=HC_MAXY, center = true);  
		cube(size=[HC_MAXX*2, HANDLEBAR_CLAMP_WIDTH * 2, HANDLEBAR_CLAMP_WIDTH], center = true);
		} //end union

		//Remove this...(cut out handlebar tube)
		cylinder (h=HANDLEBAR_CLAMP_WIDTH+1, r=HANDLEBAR_TUBE_DIAMETER/2, center=true);

		//and remove this.HANDLEBAR_CLAMP_WIDTH..(cut out BOLTs)
		ClampBoltCut (); mirror ([1,0,0]) ClampBoltCut();

		//and remove this...(to cut in half)
		translate ([-(HC_MAXX+.5),0,-(HANDLEBAR_CLAMP_WIDTH+1)/2]) cube(size=[HC_MAXX*2+1,HC_MAXY+1, HANDLEBAR_CLAMP_WIDTH+1]);

	} //end difference
} //end HandlebarClamp

module HandlebarClampDrop () {
	difference () {
		
		// Start Object: Drop mass	
		union (){
			HandlebarClamp ();  //start with another Handlebar Clamp
		
			translate ([0,0,-HANDLEBAR_CLAMP_WIDTH/2]) linear_extrude (height=HANDLEBAR_CLAMP_WIDTH) {
				hull () {
					translate ([0, -(HANDLEBAR_CLAMP_DROP_LENGTH-((HANDLEBAR_CLAMP_DROP_BOLT_DIAMETER/2)+HANDLEBAR_CLAMP_WIDTH)), 0])  circle (r=(HANDLEBAR_CLAMP_DROP_BOLT_DIAMETER/2)+HANDLEBAR_CLAMP_WIDTH);
					translate ([0,-HC_MAXY/2,(HANDLEBAR_CLAMP_WIDTH/2)]) square ([(HANDLEBAR_CLAMP_WIDTH-HANDLEBAR_CLAMP_BOLT_CAP_DIAMETER)+HANDLEBAR_TUBE_DIAMETER, HC_MAXY], center=true);
				} //end hull
			} //end linear extrude

			if (LIGHT_CLAMP_BRACKETL_MIN>BRACKETL) {
				
				translate ([0,-(HANDLEBAR_CLAMP_DROP_LENGTH-((HANDLEBAR_CLAMP_DROP_BOLT_DIAMETER/2)+HANDLEBAR_CLAMP_WIDTH)),0]) cylinder (h=(LIGHT_CLAMP_BRACKETL_MIN - BRACKETL)/2 + HANDLEBAR_CLAMP_WIDTH/2, r=(HANDLEBAR_CLAMP_WIDTH + HANDLEBAR_CLAMP_DROP_BOLT_DIAMETER/2)*.9);

			} //end if

		} //end union

		// Subtract for handlebar
		cylinder (h=HANDLEBAR_CLAMP_WIDTH+1, r=HANDLEBAR_TUBE_DIAMETER/2, center=true);

		// Subtract fot the drop bolt
		 translate ([0, -(HANDLEBAR_CLAMP_DROP_LENGTH-((HANDLEBAR_CLAMP_DROP_BOLT_DIAMETER/2)+HANDLEBAR_CLAMP_WIDTH)), 0]) cylinder (h=LIGHT_CLAMP_BRACKETL_MIN/2 + HANDLEBAR_CLAMP_WIDTH/2+1, r=HANDLEBAR_CLAMP_DROP_BOLT_DIAMETER/2, center=true);

	} //end difference

} //end HandlebarClampDrop

module LightClampBase () {
		union () {
		cylinder (h=LIGHT_CLAMP_WIDTH, r=LC_MAXY, center = true);  
		cube(size=[LC_MAXX*2, LIGHT_CLAMP_FLANGE* 2, HANDLEBAR_CLAMP_WIDTH], center = true);
		} //end union
} //end LightClamp 

module LightClampWithSupport () {
	difference () {

		//Start with a nice chunk of material...
		union (){	
			LightClampBase (); //Base material
			//Now project some of that base material in order to hull() to provide flange support
			rotate ([90,0,0]) linear_extrude (height=LIGHT_CLAMP_FLANGE) hull ()  projection (cut = false)  rotate ([-90,0,0]) LightClampBase(); //Draw material for flange support 
		} //end union	
		
		//Remove this...(cut out handlebar tube)
		cylinder (h=LIGHT_CLAMP_WIDTH+1, r=LIGHT_DIAMETER/2, center=true);

		//and remove this...(cut out BOLTs) ***These bolts are the same size as the HandlebarClamp bolts 
		LightClampBoltCut (); mirror ([1,0,0]) LightClampBoltCut();

		//and remove this...(to cut in half)
		translate ([-(LC_MAXX+.5),0,-(LIGHT_CLAMP_WIDTH+1)/2]) cube(size=[LC_MAXX*2+1,LC_MAXY+1, LIGHT_CLAMP_WIDTH+1]);

	} //end difference

} //end LightClampWithSupport

module LightClampWithBoltMount () {
	difference () {
		union () {
			LightClampWithSupport ();
			translate ([0,-(LIGHT_DIAMETER/2+LIGHT_CLAMP_BOLT_DIAMETER/2),0]) rotate ([0,90,0]) cylinder (h=BRACKETL, r=BRACKETR, center=true); //Bolt bracket
			translate ([0,-(LIGHT_DIAMETER/2+LIGHT_CLAMP_BOLT_DIAMETER/2)/2,0]) cube (size=[BRACKETL,LIGHT_DIAMETER/2+LIGHT_CLAMP_BOLT_DIAMETER/2,BRACKETR*2], center=true); //Brace under bracket
			translate ([BRACKETL/2,-(LC_MAXY)/2,BRACKETR]) rotate ([90,0,-90]) linear_extrude (height=BRACKETL) polygon(points=[ [0,0],[SUPX,0],[0,SUPY] ] ); //Bracket support top
			mirror ([0,0,1]) translate ([BRACKETL/2,-(LC_MAXY)/2,BRACKETR]) rotate ([90,0,-90]) linear_extrude (height=BRACKETL) polygon(points=[ [0,0],[SUPX,0],[0,SUPY] ] ); //bottom
		} //end union

		translate ([0,-(LIGHT_DIAMETER/2+LIGHT_CLAMP_BOLT_DIAMETER/2)-0.01,0]) rotate ([0,90,0]) cylinder (h=1+LIGHT_DIAMETER+(LIGHT_CLAMP_FLANGE-HANDLEBAR_CLAMP_BOLT_CAP_DIAMETER)/2, r=LIGHT_CLAMP_BOLT_DIAMETER/2, center=true); //Cut out Bolt Hole

		cylinder (h=LIGHT_CLAMP_WIDTH+1, r=LIGHT_DIAMETER/2, center=true);

	} //end difference

} //end LightClampWithBoltMount


//*******************************Drawing********************************

// Draw Handlebar Clamp
$fa=2; $fs=0.05;   // 

translate ([0,0,HANDLEBAR_CLAMP_WIDTH/2]) HandlebarClamp ();

translate ([0,PART_GAP,HANDLEBAR_CLAMP_WIDTH/2]) mirror ([0,1,0]) HandlebarClampDrop ();

translate ([-(PART_GAP+HC_MAXX*2),0,HANDLEBAR_CLAMP_WIDTH/2]) HandlebarClamp ();

translate ([-(PART_GAP+HC_MAXX*2),PART_GAP,HANDLEBAR_CLAMP_WIDTH/2]) mirror ([0,1,0]) HandlebarClampDrop ();

translate ([LC_MAXX + HC_MAXX + PART_GAP,0,LIGHT_CLAMP_WIDTH/2]) LightClampWithSupport ();

translate ([LC_MAXX + HC_MAXX + PART_GAP, PART_GAP, LIGHT_CLAMP_WIDTH/2]) mirror ([0,1,0]) LightClampWithBoltMount ();