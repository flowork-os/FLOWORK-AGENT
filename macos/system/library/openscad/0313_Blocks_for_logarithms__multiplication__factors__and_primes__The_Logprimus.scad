// [FL_INDEX: keywords="openscad, 3d_parametric, Blocks_for_logarithms__multiplication__factors__and_primes__The_Logprimus, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Blocks for logarithms, multiplication, factors, and primes: The Logprimus

// "Logprimus" learning blocks for logarithms, 
//   multiplication, factors, and primes
//
// by seedwire
// 11/14/2013
//

use <write/Write.scad>

// How many prime blocks?
number_of_blocks = 16; // [1:49]

// Start with this block number
block_start = 2; // [2:16]
block_start0 = block_start - 2;

// How many of each block?
number_of_each_block = 1; // [1:4]

// Stackable?
is_stackable = "yes"; // [yes,no]
stackable = (is_stackable == "yes"); 

// Which font?
selected_font = "orbitron"; // [orbitron,Letters,BlackRose,knewave,braille]
the_font = str("write/", selected_font, ".dxf");

// Ruler
make_ruler = "yes"; // [yes,no]

// High mark on ruler?
high_mark = 32; // [2:32]



/*[Hidden]*/
// Block scale (1=tiny, ...)
length_scalar = 40.0;

block_spacing = length_scalar / 6;
x = 1;
y = 1;
blocked_plate_side = sqrt(number_of_blocks);

for(iter = [0 : number_of_each_block-1])
for(n = [2 : number_of_blocks+1]) {
	assign(x = (n-2) % ceil(blocked_plate_side), y = floor((n-2) / blocked_plate_side)) { 

	  	translate([iter*((1+ceil(blocked_plate_side)*(0.4 * 					  length_scalar + block_spacing))) 
						+
					  x *(0.4 * length_scalar + block_spacing), 
				     y * (0.4 * length_scalar + block_spacing), 
				     0])
		 color([x / blocked_plate_side, 0.7 * y / blocked_plate_side, x%y / blocked_plate_side / blocked_plate_side]) block(n+block_start0, [0.4 * length_scalar ,0.4 * length_scalar]);
	}
}

// Build the ruler
if(make_ruler == "yes") {
	difference() { 
		translate([-2, (-0.4*1.25*length_scalar) - block_spacing, 0]) cube([length_scalar * log(high_mark)+2,1.25*0.4*length_scalar,2]);
		union() { 
			translate([0, (-0.4*1.25*length_scalar) - block_spacing+2, 1]) cube([length_scalar * log(high_mark)+1,1.25*0.4*length_scalar-4,2]);
		for(n = [2 : high_mark]) {
			if(n % 10 == 0) { 
				translate([log(n)*length_scalar, (-0.4*1.25*length_scalar) - block_spacing+0.5, 0.75]) cube([0.35,1.25*0.4*length_scalar-1,2]);			} else {
				translate([log(n)*length_scalar, (-0.4*1.25*length_scalar) - block_spacing+1, 0.75]) cube([0.35,1.25*0.4*length_scalar-2,2]);
				}
			}
		}
	}

}

module block(integer, section, center)
{
	the_str = str(integer);
	difference () { 
		difference() {
			union() { 
				if(stackable) {
					difference() { 
						block0(integer, section, center);
						translate([section[0]/2,section[0]/2, (log(integer)*length_scalar) + section[0]/15]) cylinder(h=10, r=3.3, center=true); // a peg hole
					}
				} else {
					block0(integer, section, center);
				}
			}
			if(stackable) { translate([0,0, -(log(integer)*length_scalar) + section[0]/15]) block0(integer, section, center);									
									}
		}
		union() { writecube(t=3, h=section[0]/2.5, face="front", text=the_str, where=[section[0]/2, section[1]/2, ((log(integer)*length_scalar) - section[1]/8)/2], size=[section[0], section[1], (log(integer)*length_scalar) - section[1]/8], font=the_font);
		writecube(t=3, h=section[0]/2.5, face="back", text=the_str, where=[section[0]/2, section[1]/2, ((log(integer)*length_scalar) - section[1]/8)/2], size=[section[0], section[1], (log(integer)*length_scalar) - section[1]/8], font=the_font);
		writecube(t=3, h=section[0]/2.5, face="left", text=the_str, where=[section[0]/2, section[1]/2, ((log(integer)*length_scalar) - section[1]/8)/2], size=[section[0], section[1], (log(integer)*length_scalar) - section[1]/8], font=the_font);
		writecube(t=3, h=section[0]/2.5, face="right", text=the_str, where=[section[0]/2, section[1]/2, ((log(integer)*length_scalar) - section[1]/8)/2], size=[section[0], section[1], (log(integer)*length_scalar) - section[1]/8], font=the_font);
		}
	}
	translate([section[0]/2,section[0]/2, 0]) cylinder(h=10, r=3); // a peg

}


module block0(integer, section, center)
{
	if(stackable) {
		hull() { 
			cube([section[0], section[1], (log(integer)*length_scalar) - section[1]/8], center=center);
			union() {translate([section[0]/5, section[0]/5, (log(integer)*length_scalar) - section[0]/8]) sphere(r=section[0]/8+1);
		}		
			translate([section[0]-section[0]/5, section[0]/5, (log(integer)*length_scalar) - section[0]/8]) sphere(r=section[0]/8+1);

			translate([section[0]-section[0]/5, section[0]-section[0]/5, (log(integer)*length_scalar) - section[0]/8]) sphere(r=section[0]/8+1);

			translate([section[0]/5, section[0]-section[0]/5, (log(integer)*length_scalar) - section[0]/8]) sphere(r=section[0]/8+1);
		  }
	} else {
		// The very simplest...
		cube([section[0], section[1], (log(integer)*length_scalar) - section[1]/8], center=center);
	}
}

