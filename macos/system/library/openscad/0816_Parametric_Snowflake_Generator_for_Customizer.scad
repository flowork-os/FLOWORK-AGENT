// [FL_INDEX: keywords="openscad, 3d_parametric, Parametric_Snowflake_Generator_for_Customizer, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Parametric Snowflake Generator for Customizer

//Parametric Snowflake Generator by Gringer Thing:39685

edge_length = 22;//[10:22]
flake_thickness=2;//[2:5]

extrude_width=10;//[1:10]
//multiplied by 4
number_of_crystals = 3; // [1:5]

backbone_width= 1; // [1:5]
el=edge_length;
ft=flake_thickness;
cmt=edge_length / 5;
xw=extrude_width/10;
nc=number_of_crystals*4;
bw=backbone_width;
cit = xw; // 
th = sqrt(3) * el/2; // triangle height
rv = rands(0,1,nc*5); // random vector (x, y, length, direction, thickness)


// the idea on how to do this is loosely based on origami snowflakes as at:
// http://www.marthastewart.com/276331/how-to-make-paper-snowflakes
// combined with Wilson Bentley's observations of snowflakes
// http://en.wikipedia.org/wiki/Wilson_Bentley

module flake_part(){
	rotate([0,0,30]) translate([0,-el/2,0])
		cube([bw,el,ft], center = true);
	for(i = [0:nc-1]){
		assign(yr = sqrt(rv[i*4]),
		   xr = rv[i*4+1] * sqrt(rv[i*4]),
		   rt = (rv[i*4+2]<(1/3))?0:(rv[i*4+2]<(2/3))?60:120,
		   sl = rv[i*4+3],
		   ct = (rv[i*4+4])*(rv[i*4+4])){
			if(((rt != 120) || (yr + sl/2 < 1)) && (sl*el/2 > xw)){
				translate([xr*el/2, -yr*th,0]) rotate(rt)
					cube([sl*el/2, cit + max(0,cmt*ct/2-cit), ft], 
					   center = true, $fa = 60);
			}
		}
	}
}

for(ri = [0:60:300]){
	rotate([0,0,ri]) flake_part();
	rotate([0,180,ri]) flake_part();
}