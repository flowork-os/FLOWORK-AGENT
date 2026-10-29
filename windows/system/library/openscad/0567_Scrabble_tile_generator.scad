// [FL_INDEX: keywords="openscad, 3d_parametric, Scrabble_tile_generator, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Scrabble tile generator

// scrabble tile generator, Glyn Cowles, revised Oct 2018
letter="A";
number="1";
sfont="Consolas";
/* [Hidden] */
ht=6.28; // tile height
x=18.9;  //  size
y=20.2;
dp=.6; // letter depth		
lz=13; // letter size;
nz=4; // number size  
$fn=50;
//----------------------------------------------------------------------

difference() {
	roundedRect([x,y,ht],1);
	if (number == "10") {
		#translate([1.5,5,ht-dp]) linear_extrude(dp)
            text(letter,size=lz,font=sfont);	
		#translate([13,2.5,ht-dp]) linear_extrude(dp)
            text(number,size=nz-1,font=sfont);
	}
	else {
			#translate([3,5,ht-dp]) linear_extrude(dp)
            text(letter,size=lz,font=sfont);	
		#translate([14,3,ht-dp]) linear_extrude(dp)
            text(number,size=nz,font=sfont);
	}
	translate([x/2,y/2,-2]) cylinder(r=8,h=4);
}

//----------------------------------------------------------------------
module roundedRect(size, radius) {
x = size[0];
y = size[1];
z = size[2];

linear_extrude(z)
hull() {
translate([radius, radius, 0])
circle(r=radius);

translate([x - radius, radius, 0])
circle(r=radius);

translate([x - radius, y - radius, 0])
circle(r=radius);

translate([radius, y - radius, 0])
circle(r=radius);
}
}