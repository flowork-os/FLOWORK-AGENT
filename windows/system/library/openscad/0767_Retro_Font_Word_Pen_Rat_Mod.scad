// [FL_INDEX: keywords="openscad, 3d_parametric, Retro_Font_Word_Pen_Rat_Mod, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Retro Font Word Pen Rat Mod

// Derived from thing: http://www.thingiverse.com/thing:45576
//   on 2-2-2013 by TheBogueRat
// Things to do...
// Add font selection.
//

use <MCAD/fonts.scad> //Must have OpenSCAD ver 2013.01.22 or you'll have compile errors.

// CREATION OPTIONS (true or false; no caps)
create_pen = true;
create_stub = true;
create_cap = true;
create_clip = true;


// DIMENSIONAL VARABLES
// Word to display on the pen
word = "AWESOME";

// Scale multipler for font size //2.1
font_scale = 2.2	;

// Character Spacing (for some reason this value is buggy using the customizer) //.8
font_spacing = 0.9; 

// The diameter of end hole // 4.3*1
pen_inner_diameter = 4.3 *1;
pen_inner_radius = pen_inner_diameter / 2;

// length of the entire pen //130
pen_length = 130; //

// Overal thickness of the pen //8
pen_thickness = 8*1;

// Starting distance for finger grip  //10 is a nice start
font_start_dist = 7;

// Stub length that goes into the end 
stub_length = pen_thickness + 0;

// End cap length that will show
end_length = pen_thickness + 0;

// Length of the cap if selected.  Less than 20 and the cap will not work.  20mm is about the average length of this design plus the inserted pen tip.
	cap_length = 25;



/////////////////////////////////////////
//////////////////////////////////


module penword()
{

thisFont=8bit_polyfont();
x_shift=thisFont[0][0] * font_spacing;
y_shift=thisFont[0][1];

	theseIndicies=search(word,thisFont[2],1,1);
	wordlength = (len(theseIndicies))* x_shift;
	
	difference() {

		union() {

// Create the Text //
			scale([font_scale,font_scale,1]){
			for( j=[0:(len(theseIndicies)-1)] ) 
				// translate([ j*x_shift + 1, -y_shift/2 ,-pen_thickness/2]) 
				translate([ j*x_shift + font_start_dist, -y_shift/2 ,-pen_thickness/2]) 
				{
					linear_extrude(height=pen_thickness) polygon(points=thisFont[2][theseIndicies[j]][6][0],paths=thisFont[2][theseIndicies[j]][6][1]);
				}
			}
			
// Main body
			translate([1*font_scale+3	,-y_shift*.45,-pen_thickness/2]) cube([pen_length - 3,y_shift * 0.9,pen_thickness * 0.8]);

// Pen Tip
			rotate(a=[0,90,0]) 
				{
					translate([pen_thickness*0.1,0,0	])	cylinder(h = 5, r = pen_thickness*.4, $fn=50);
					translate([pen_thickness*0.1,0,-5	])	cylinder(h = 5, r1 = 1, r2 = pen_thickness*.4, $fn=50);
				}			
		}
// Cut outs
			translate([0,-pen_inner_diameter/2,-pen_thickness/2+pen_thickness*.15]) cube([pen_length + 20,pen_inner_diameter,pen_inner_diameter]);
			rotate(a=[0,90,0])translate([pen_thickness*.1,0,-15])	cylinder(h = 30, r = pen_inner_radius, $fn=100);
	}
}  //end penword

// Create end stub if desired
if (create_stub == true) {
	union(){
		// End Cap
		rotate([0,90,0]) translate([-pen_thickness/2-(end_length-pen_thickness), 10, 0]) cube([end_length, pen_thickness, pen_thickness*0.8]);
		// Stub (5% smaller than inner_diameter)
		rotate([0,90,0]) translate([-stub_length-(end_length-pen_thickness),10+(pen_thickness/2)-(pen_inner_diameter*0.95/2),pen_thickness*.15]) cube([stub_length+1,pen_inner_diameter*0.95,pen_inner_diameter*0.95]);
	}
} // end of end stub

// Create cap with clip if desired.
if (create_cap == true && create_clip == false){
		difference(){
			// Outer Shell
			translate([20-pen_thickness,15-pen_thickness/2,-pen_thickness/2]) cube([pen_thickness,pen_thickness, cap_length]);
			// Remove Innards
			translate([20-pen_thickness/2,15,-pen_thickness/2+cap_length-19.9]) cylinder(h = cap_length,r = pen_thickness*0.8/2,$fn=100);
	}
} // end of clip only

// Create cap without a clip if desired.
if (create_cap == true && create_clip == true) {
	union(){
		difference(){
			// Outer Shell
			translate([20-pen_thickness,15-pen_thickness/2,-pen_thickness/2]) cube([pen_thickness,pen_thickness, cap_length]);
			// Remove Innards (5% larger diameter than pen tip)
			translate([20-pen_thickness/2,15,-pen_thickness/2+cap_length-19.9]) cylinder(h = cap_length,r = pen_thickness*0.90/2,$fn=100);
		}
	// Add the clip (5% smaller than inner diameter for press fit)
	translate([20,13,-pen_thickness/2]) cube([3,4,4]);
	translate([21.5,13,-pen_thickness/2]) cube([1.5,4,19]);
	translate([21.75,17,-pen_thickness/2+19])rotate([90,0,0])cylinder(h=4, r=1.25, $fn=100);
	}
} // end of cap & clip

if (create_pen == true) {
penword();
}