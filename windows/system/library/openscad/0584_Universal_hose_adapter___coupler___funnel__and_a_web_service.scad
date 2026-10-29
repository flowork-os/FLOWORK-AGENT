// [FL_INDEX: keywords="openscad, 3d_parametric, Universal_hose_adapter___coupler___funnel__and_a_web_service, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Universal hose adapter & coupler & funnel, and a web service

//
// universal_hose_adapter.scad
//
// By Jérémie FRANCOIS / MoonCactus / contact@tecrd.com
//
// Check the webservice on http://www.tecrd.com/page/liens/universal_hose_adapter (temporary URL)
//

// Respect the three-slashes and var=val syntax for the web service to work!
/// title=Lower cone
cone1_min=28;				/// unit=mm		| min=1		| label=Base radius | comment=The outside of the lower cone. Usually equal or slightly smaller than the top radius, unless you want to make a funnel!
cone1_max=32;				/// unit=mm		| min=1		| label=Top radius | comment=Usually equal or slightly bigger than the base radius, unless you want to make a funnel!
cone1_height=20;			/// unit=mm		| min=0		| label=Height
cone1_wall=2;				/// unit=mm		| min=0.1	| label=Wall thickness
cone1_barb_width=0;			/// unit=mm		| min=0		| label=Barb size | comment=The protuding width of barb-like outer rings to prevent the hose from slipping. Set to zero to disable.

/// title=Top cone
cone2_max=18;				/// unit=mm		| min=1		| label=Base radius | comment=Usually equal or slightly bigger than the top radius.
cone2_min=15;				/// unit=mm		| min=1		| label=Top radius | comment=The outside of the upper cone. Usually equal or slightly smaller than the base radius.
cone2_height=30;			/// unit=mm		| min=1		| label=Height
cone2_wall=2;				/// unit=mm		| min=0.1	| label=Wall thickness
cone2_barb_width=0.8;		/// unit=mm		| min=0		| label=Barb size | comment=The protuding width of barb-like outer rings to prevent the hose from slipping. Set to zero to disable.

/// title=Common properties
join_height=3;				/// unit=mm		| min=0		| label=Junction height | comment=How tall is the connection between the two cones. Make sure it is thick enough so as to avoid excessively thin walls and/or steep inner overhang. Twice the wall thickness is a good starting value.

barb_flatness_ratio=2;		/// unit=ratio	| min=0.1	| max=5		| label=Barb flatness ratio | comment=Sets barb height as a factor of barb size. Eg. 1.0 means a 1:1 x/y aspect ratio (aka 45°), and 2.0 makes a flatter barb.
barb_spacing_ratio=2;		/// unit=ratio	| min=0		| max=5		| label=Barb spacing ratio| comment=Sets barb spacing as a factor of barb height. So 0 means adjacent barbs, and 1 give an identical flat space as the barbs themselves.
barb_skew_ratio=0.15;		/// unit=ratio	| min=-0.2	| max=1.2	| label=Barb symetry ratio | comment=Avoid overhang by using a strictly positive value (easier print). Symetrical barbs correspond to 0.5. Negative values give concave barbs, and makes sense only for the lower cone. Values higher than 0.5 lead to reversed barbing (probably useless).
check_guts=0;				///	unit=flag	| min=0		| max=1		| label=Explode the shape | comment=This is only useful to double-check the objet shape and walls before printing (like the illustration on the left).


// $fa=10;		// how fine the curved objets are (max angle between broken parts)
tol=0.05;	// tolerance (mostly useful for openscad preview)

function xpos(rmin, rmax, height, hpos) = ( rmin+(rmax-rmin)*hpos/height )/2;

module hollow_cone(rmin, rmax, height, wall, barb_width) // TODO: spokes
{
	if(rmin>0 && rmax>0 && height>0)
	{
		// Hollow cone body
		difference()
		{
			cylinder(r1=rmin/2, r2=rmax/2, h=height);
			if(wall>0)
				translate([0,0,-tol])
					cylinder(r1= rmin/2-wall, r2= rmax/2-wall, h=height+2*tol);
		}
		// Babed-like rings
		if(barb_width>0 && barb_flatness_ratio!=0)
		{
			for(bs=[barb_width*barb_flatness_ratio : 1 : barb_width*barb_flatness_ratio]) // this is just to simulate a "local" variable... :(
			{
				for(hpos=[
					bs/2
					: barb_width * barb_flatness_ratio * (1 + barb_spacing_ratio)
					: height - bs/2]
				)
				{
					translate([0,0,hpos])
					rotate_extrude()
						polygon( points=[
							[xpos(rmin,rmax,height,hpos)-tol, 0],
							[xpos(rmin,rmax,height,hpos + bs*(1-barb_skew_ratio)) + barb_width, bs * (1-barb_skew_ratio)],
							[xpos(rmin,rmax,height,hpos + bs)-tol, bs],
						] );
				}
			}
		}
	}
}

	difference()
	{
		union()
		{
			color([1,0,0])
			hollow_cone(cone1_min, cone1_max, cone1_height, cone1_wall, cone1_barb_width);

			color([0,0,1])
				translate([0,0,cone1_height+join_height+cone2_height])
					rotate([180,0,0])
						hollow_cone(cone2_min, cone2_max, cone2_height, cone2_wall, cone2_barb_width);

			// intermediate section
			if(join_height>0)
			{
				color([0,1,0])
				translate([0,0,cone1_height])
				rotate_extrude()
					polygon( points=[
						[ cone1_max/2-cone1_wall, 0],
						[ cone1_max/2, 0],
						[ max(cone1_max,cone2_max)/2, join_height/2],
						[ cone2_max/2, join_height],
						[ cone2_max/2-cone2_wall, join_height],
						[ min(cone1_max/2-cone1_wall,cone2_max/2-cone2_wall), join_height/2],
					] );
			}
		}

		if(check_guts!=0)
			translate([0,0,-tol]) cube([100,100,100]);		// Just to show the interior!
	}