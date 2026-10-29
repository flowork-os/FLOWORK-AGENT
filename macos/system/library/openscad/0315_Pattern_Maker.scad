// [FL_INDEX: keywords="openscad, 3d_parametric, Pattern_Maker, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Pattern Maker

length=60; //[20:100] 
width =50;  //[20:100] 
pattern_thickness=3;//[3:10]

sides=4;//[3:Triangle (3-sided),4:Square (4-sided),5:Pentagon (5-sided),6:Hexagon (6-sided),7:Heptagon (7-sided),8:Octogon (8-sided),9:Nonagon (9-sided),10:Decagon (10-sided),11:Hendecagon (11-sided),12:Dodecagon (12-sided),30:Circle (3w0-sided)]
radius=6;//[2:25]
polygon_edge_thickness=2;//[1.0:10.0]
overlap_factor=10; //[0:100]
polygon_rotation=40;//[0:120]
stretch_off_on=0;//[0:OFF, 1:ON]
//% X stretch.
polygon_stretch=100;//[-20:100]




HONEYCOMB(width,length,9,radius,overlap_factor,polygon_edge_thickness,sides,polygon_stretch);
					

module HONEYCOMB(w,l,h,r,overlapFactor,polyEdge,sides,stretch,){
columns =l/(r*3)+1;
rows = w/(r*sqrt(3)/2*2)+3;

//translate([-w/1.3,l/1.8,pattern_thickness])
translate([-w,-l/2,pattern_thickness])

//rotate([0,0,-90])
	for(y = [1:rows-1]){
		translate([0,r*sqrt(3)/2*y*2,0])
		scale([pow(1+y/(21),0),1,1])
		for(x = [1:columns-1]){
			translate([r*x*3,0,0])
			for(i = [0:1]){
				translate([r*1.5*i,r*sqrt(3)/2*i,0])
				rotate([0,0,polygon_rotation])
				difference(){
					if(sides < 5){
						scale([1,pow((stretch+100)/100,stretch_off_on),1])
						cylinder(h=2*pattern_thickness, r = r+polyEdge+(r*overlapFactor/50), center = true, $fn = sides);
					} else {
						scale([1,pow((stretch+100)/100,stretch_off_on),1])
						cylinder(h=2*pattern_thickness, r = r+(r*overlapFactor/50), center = true, $fn = sides);
					}
					scale([1,pow((stretch+100)/100,stretch_off_on),1])
					cylinder(h=2.05*pattern_thickness, r = r-polyEdge+(r*overlapFactor/50), center = true, $fn = sides);
				}
			}
		}
	}
}
//derived from Customizable Necktie by Keenan, published	 Mar 2, 2013
//http://www.thingiverse.com/thing:56209




			
				