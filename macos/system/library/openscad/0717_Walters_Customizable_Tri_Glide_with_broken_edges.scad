// [FL_INDEX: keywords="openscad, 3d_parametric, Walters_Customizable_Tri_Glide_with_broken_edges, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Walters Customizable Tri Glide with broken edges

// License: Public Domain

//=== Flat Tri Glide ===//

//width of the webbing opening (1in = 25.4 mm)
_1_webbingOpeningWidth = 38;

// width of the gap for the webbing
_2_webbingGapWidth = 6;

// width of the side edges
_3_sideEdgeWidth = 5;

// width of the main edges
_4_mainEdgeWidth = 7;

// width of the center beam
_5_centerWidth = 10;

// overall thickness of the tri glide
_6_overallHeight = 4; //3

// percent corner rounding
_7_cornerRoundingPercent = 50; // [1:100]

// how much to break off the edges (in mm)
_8_cornerBreakage = 0.75;


module makeBody(xsize, ysize, height, radius) {
	translate([0,0,height/2]) {
		minkowski() {
			cube(size=[xsize-2*radius,ysize-2*radius, height/2], center = true);
			cylinder(r=radius, h=height/2, center=true);
		}
	}
}

module makeCuts(width, gap, thickness, height,b) {
	offset = (thickness+gap)/2;
	for (y = [-offset, offset]) {
		translate([0, y, 0]) {

			translate([0, 0, height/2])
				cube(size=[width, gap, height*2], center=true);
			translate([0, 0, 0])
				makeCutEnd(width, gap, thickness, height,b);
			translate([0, 0, height]) scale([1,1,-1])
				makeCutEnd(width, gap, thickness, height,b);
		}
	}
}

module makeCutEnd(width, gap, thickness, height,b)
{
	hull(){
		translate([0,0,+b/2])
			cube(size=[width, gap, b], center=true);
		translate([0,0,-b/2])
			cube(size=[width+2*b, gap+2*b, b], center=true);			
	}
}

module makeTriGlide(width, gap, edgeThicknessSide, edgeThicknessMain, centerThickness, height, rounding, b, $fn=90) {
	xsize = width + edgeThicknessSide * 2;
	ysize = centerThickness + edgeThicknessMain * 2 + gap * 2;
	radius = max(edgeThicknessSide,edgeThicknessMain)*(rounding/100);
	difference() {
        hull()
        {
		  makeBody(xsize-2*b, ysize-2*b, height, radius);
          translate([0,0,b])
		  makeBody(xsize, ysize, height-2*b, radius);
        }
		makeCuts(width, gap, centerThickness, height,b);
	}
}


makeTriGlide
  ( _1_webbingOpeningWidth
  , _2_webbingGapWidth
  , _3_sideEdgeWidth
  , _4_mainEdgeWidth
  , _5_centerWidth
  , _6_overallHeight
  , _7_cornerRoundingPercent
  ,_8_cornerBreakage
  );