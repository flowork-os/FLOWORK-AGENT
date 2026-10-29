// [FL_INDEX: keywords="openscad, 3d_parametric, PCB_Support, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: PCB Support

/* pcb_box_slide_with_tabs.scad
 * By Nicholas C Lewis - Jan 1, 2011
 * http://www.thingiverse.com/thing:5396 
 *
 * derived from pcb_box_slide.scad 
 *     Parametric, open PCB-box (slide-in) by chlunde
 *     http://www.thingiverse.com/thing:4071
 *
 * CHANGES
 * - adjusted to fit Arduino Mega
 * - added mounting tabs
 * - turned off cutouts
 * - adjusted bottom cutout size
 */

//CUSTOMIZER VARIABLES
// PCB width
pcb_width_text_box = 100;
// PCB length
pcb_length_text_box = 150;
// PCB height
pcb_height_text_box = 1.62;
// PCB bottom margin
pcb_bottom_margin_text_box = 2.5;
// Wall width tick
wall_width_thick_text_box = 3.5;
// Tab hole radius
tab_hole_radius_text_box = 4;
// Tab outer radius
tab_outer_radius_text_box = 7;
// Box height
box_height_text_box = 10;
//CUSTOMIZER VARIABLES END

pcb_width = pcb_width_text_box;
pcb_length = pcb_length_text_box;
pcb_height = pcb_height_text_box;
slisse = 1;

pcb_bottom_margin = pcb_bottom_margin_text_box;
wall_width_thick = wall_width_thick_text_box;
wall_width = wall_width_thick-slisse;
box_height = box_height_text_box;

//tab parameters
tab_hole_radius=tab_hole_radius_text_box;
tab_outer_radius=box_height_text_box;



module tab() {
	difference(){
		union() {
			translate([-tab_outer_radius,-tab_outer_radius,0])
			cube([tab_outer_radius,2*tab_outer_radius,wall_width]);
			translate([-tab_outer_radius,0,0])
				cylinder(r=tab_outer_radius, h = wall_width);
		}
		translate([-tab_outer_radius,0,0])
		cylinder(r= tab_hole_radius, h = wall_width+3,center=true);
	}

}

module box() {
  union() {
    cube([pcb_width + 2*wall_width, pcb_length + 2*wall_width, wall_width]);

    cube([wall_width_thick, pcb_length + 2*wall_width, box_height]);

    cube([pcb_width + 2*wall_width, wall_width_thick, box_height]);

    %translate([0, pcb_length+wall_width, 0])
      cube([pcb_width + 2*wall_width,wall_width,box_height]);

    translate([pcb_width + wall_width - slisse,0,0])
      cube([wall_width_thick, pcb_length + 2*wall_width, box_height]);
  }
//comment out this part to remove tabs
 for(i=[tab_outer_radius,(pcb_length + 2*wall_width)/2,pcb_length + 2*wall_width-tab_outer_radius]){
	translate([0,i,0])tab();
	translate([pcb_width + 2*wall_width,i,0])mirror()tab();
 }


}

module pcb() {
  translate([wall_width, wall_width, wall_width + pcb_bottom_margin])
    cube([pcb_width,pcb_length + wall_width + 0.1,pcb_height]);
  translate([wall_width, wall_width, wall_width + pcb_bottom_margin+pcb_height])rotate([0,45,0])
    cube([pcb_height,pcb_length + wall_width + 0.1,pcb_height]);
  translate([wall_width+pcb_width-2*cos(45)*pcb_height, wall_width, wall_width + pcb_bottom_margin+pcb_height])rotate([0,45,0])
    cube([pcb_height,pcb_length + wall_width + 0.1,pcb_height]);
  translate([wall_width_thick, wall_width, wall_width + pcb_bottom_margin])
    cube([pcb_width-2*slisse,pcb_length + wall_width + 0.1,box_height]);

}



module holes() {
  *translate([wall_width + pcb_width/2, wall_width_thick + 0.1, pcb_width/2+wall_width])
    rotate(a=90,v=[1,0,0])
      cylinder(r=pcb_width/2, h=wall_width_thick + 0.2);

  *translate([-0.1, wall_width + pcb_length/2, pcb_length/2 + wall_width])
    rotate(a=90,v=[0,1,0])
      cylinder(r=pcb_length/2, h=wall_width_thick + 0.2);

  *translate([pcb_width + wall_width - slisse - 0.1, wall_width + pcb_length/2, pcb_length/2 + wall_width])
    rotate(a=90,v=[0,1,0])
      cylinder(r=pcb_length/2, h=wall_width_thick + 0.2);

 * translate([pcb_width/2 + wall_width, wall_width + pcb_length/2, -0.1])
    rotate(a=0,v=[0,1,0])
      cylinder(r=min(pcb_length,pcb_width)/2 - wall_width/2, h=wall_width_thick + 0.2);
   
  inner_margin = 9;
  translate([inner_margin +wall_width, inner_margin+wall_width, -0.1])
    cube([pcb_width-inner_margin*2,pcb_length -inner_margin*2,wall_width + 0.2]);
}

difference() {
  box();
  pcb();
  holes();
}

* color([1,0,0])
  translate([pcb_width/2 + wall_width, wall_width + pcb_length/2, -0.1])
    rotate(a=0,v=[0,1,0])
      cylinder(r=min(pcb_length,pcb_width)/2 - wall_width/2, h=wall_width_thick + 0.2);

