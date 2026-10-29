// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_Lissajous_Picture_Frame__v1_0, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable Lissajous Picture Frame, v1.0 

/* Customizable Lissajous Picture Frame by REML, v1.0                   */
/* CreativeCommons: Attribution - Non-Commercial - ShareAlike           */
/* Lissajous Knot by REML, built with polymaker's 2D Graphing Functions */

/* For more information on Lissajous Curves:          */
/* http://gerdbreitenbach.de/lissajous/lissajous.html */
/* http://mathworld.wolfram.com/LissajousCurve.html   */

//preview[view:north, tilt:bottom]

/* Parametric Frame */

/* Parameters */

/* I kept the Customizer Parameters to just the Lissajous elements, but you can adjust the lattice frame and other items below. */

//Individual lattice pane size in mm: 
lissajous_pane=1*26; //[26:55]
//Thickness of the lattice frame bars.
muntin=1*.85; //[.85:Thinnish, .8:Thick, .75:Thicker]
inner_box=lissajous_pane*muntin;
x_offset=inner_box+((lissajous_pane-inner_box)/2);
y_offset=x_offset;
bounds=lissajous_pane+(3*x_offset);
shift=-1*((bounds/2)-(lissajous_pane/2));
echo ("inner_box=", inner_box, "bounds=", bounds, "shift=", shift);
picture_box=1.85*lissajous_pane;

/* lissajous parametric equation */
pi = 1*3.14159;
//Frequency of the 1st curve:
first_wave=2; //[2:15]
//Frequency of the 2nd curve:
second_wave=3; //[2:15]
//steps for Lissajous Curve:
smoothing=250; //[100:300]
//of curves compared to lattice pane size:
lissajous_scale=100; //[100:200]
scale_curves=(lissajous_pane/26)*(lissajous_scale/10)+2;
echo ("scale_curves",scale_curves);
function x(t) = sin(first_wave*(t+pi));
function y(t) = sin(second_wave*t);

/* LISSAJOUS COMBOS

	4,6,300 combo failed
4,6,250 good
	3,6,250 ok but needs 90deg rotation
6,3,250 fixes rotation issue of 3,6
6,9,250 ok
	1,2 - DUH - looks just like 3,6
	3,2 - very springy, but needs the rotation
2,3 - works
	3,4 - needs rotation
4,3 - good
	5,4 - heavy, needs rotation
	4,5,250 - fails - good looking F5 but empty on F6
	4,5,200 - fails
	4,5,300 - fails (CGAL error in CGAL_Build_PolySet: CGAL ERROR: assertion violation!
	Expr: check_protocoll == 0
	File: /home/bpitcher/openscad_deps/mxe/usr/lib/gcc/i686-pc-mingw32/4.7.2/../../../../i686-pc-mingw32/include/CGAL/Polyhedron_incremental_builder_3.h
	Line: 199)
	8,9 - a mess
7,9,250 - ok, dense, coarse
	7,9,300 - not better
	7,9,150 - ugly
9,13,250 - ok, dense
9,15 (3,5) - funky pretzel
7,15 - ok - super dense chex
	13,15,250 - abstract hot mess
13,15,100 150scale - kid scribble (needs scaling or will not join to lattice)
	7,11 - hot mess

*/

/* surround frame array functions */

function trans_x(p)=lookup(p, [
	[1, 0],
	[2, x_offset],
	[3, 2*x_offset],
	[4, 3*x_offset],
	[5, 0],
	[6, 0],
	[7, 0],
	[8, x_offset],
	[9, 2*x_offset],
	[10, 3*x_offset],
	[11, 3*x_offset],
	[12, 3*x_offset]
	]);

function trans_y(p)=lookup(p, [
	[1, 0],
	[2, 0],
	[3, 0],
	[4, 0],
	[5, y_offset],
	[6, 2*y_offset],
	[7, 3*y_offset],
	[8, 3*y_offset],
	[9, 3*y_offset],
	[10, 3*y_offset],
	[11, y_offset],
	[12, 2*y_offset]
	]);

function rota(p)=lookup(p, [
	[1,45],
	[2,90],
	[3,90],
	[4,135],
	[5,0],
	[6,0],
	[7,-45],
	[8,-90],
	[9,-90],
	[10,-135],
	[11,180],
	[12,180]
	]);

/* shift entire model to center & flip to lay flat on build platform */

rotate ([180,0,180]) translate ([shift,shift,0])	{

/* join lissajous, lattice frame and picture box */
union ()	{

/* lattice surround */

for (L=[1:12])	{
	translate ([trans_x(L),trans_y(L),0])	{
	difference ()	{
		cube([lissajous_pane,lissajous_pane,3], center=true);
			cube([inner_box,inner_box,3.5], center=true);
		}
	}
}

/* lissajous surround */

for (L=[1:12])	{
echo (L,trans_x(L),trans_y(L),rota(L));
	translate ([trans_x(L),trans_y(L),0])	{
		rotate ([0,0,rota(L)])	{
			translate (0,0,-5)	{
				scale(v=[scale_curves, scale_curves, 10]) {
					linear_extrude(height=0.15)
						2dgraph([10, 1450], th=0.1, steps=smoothing, parametric=true);
				}
			}
		}
	}
}

/* picture box */	

color ([1,0,0])	{
	translate ([abs(shift),abs(shift),-5.05])	{
		difference ()	{
			cube([picture_box,picture_box,10], center=true); // outer box
				translate ([0,0,2])	cube([picture_box-2,picture_box-2,10], center=true); // main hollow
				translate ([0,-5,-5])	cube([picture_box*.8,picture_box*.9,8], center=true); // back wall cutout
				translate ([0,-x_offset,-4])	cylinder(h=10,r=(picture_box-2)/2,center=true, $fn=100); // bottom edge cutout
				translate ([0,x_offset-12,0])	cylinder(h=15,r=10,center=true, $fn=4); //nail notch
		}
		
/* corner muntins for picture box glass */

		translate ([0,0,5])	{
			difference ()	{
			rotate ([0,0,22.5])	cylinder (h=2.85, r=(picture_box/1.92)*(1.92-muntin), center=true, $fn=8);
			rotate ([0,0,22.5])	cylinder (h=3.1, r=(picture_box/1.92), center=true, $fn=8);
			}
		}
	}
}
} // top level union
} // top level rotate

/*****************************************************************************
* 2D Graphing Functions by polymaker: http://www.thingiverse.com/thing:11243 *
******************************************************************************/

// These functions are here to help get the slope of each segment, and use that to find points for a correctly oriented polygon
function diffx(x1, y1, x2, y2, th) = cos(atan((y2-y1)/(x2-x1)) + 90)*(th/2);
function diffy(x1, y1, x2, y2, th) = sin(atan((y2-y1)/(x2-x1)) + 90)*(th/2);
function point1(x1, y1, x2, y2, th) = [x1-diffx(x1, y1, x2, y2, th), y1-diffy(x1, y1, x2, y2, th)];
function point2(x1, y1, x2, y2, th) = [x2-diffx(x1, y1, x2, y2, th), y2-diffy(x1, y1, x2, y2, th)];
function point3(x1, y1, x2, y2, th) = [x2+diffx(x1, y1, x2, y2, th), y2+diffy(x1, y1, x2, y2, th)];
function point4(x1, y1, x2, y2, th) = [x1+diffx(x1, y1, x2, y2, th), y1+diffy(x1, y1, x2, y2, th)];
function polarX(theta) = cos(theta)*r(theta);
function polarY(theta) = sin(theta)*r(theta);

module nextPolygon(x1, y1, x2, y2, x3, y3, th) {
	if((x2 > x1 && x2-diffx(x2, y2, x3, y3, th) < x2-diffx(x1, y1, x2, y2, th) || (x2 <= x1 && x2-diffx(x2, y2, x3, y3, th) > x2-diffx(x1, y1, x2, y2, th)))) {
		polygon(
			points = [
				point1(x1, y1, x2, y2, th),
				point2(x1, y1, x2, y2, th),
				// This point connects this segment to the next
				point4(x2, y2, x3, y3, th),
				point3(x1, y1, x2, y2, th),
				point4(x1, y1, x2, y2, th)
			],
			paths = [[0,1,2,3,4]]
		);
	}
	else if((x2 > x1 && x2-diffx(x2, y2, x3, y3, th) > x2-diffx(x1, y1, x2, y2, th) || (x2 <= x1 && x2-diffx(x2, y2, x3, y3, th) < x2-diffx(x1, y1, x2, y2, th)))) {
		polygon(
			points = [
				point1(x1, y1, x2, y2, th),
				point2(x1, y1, x2, y2, th),
				// This point connects this segment to the next
				point1(x2, y2, x3, y3, th),
				point3(x1, y1, x2, y2, th),
				point4(x1, y1, x2, y2, th)
			],
			paths = [[0,1,2,3,4]]
		);
	}
	else {
		polygon(
			points = [
				point1(x1, y1, x2, y2, th),
				point2(x1, y1, x2, y2, th),
				point3(x1, y1, x2, y2, th),
				point4(x1, y1, x2, y2, th)
			],
			paths = [[0,1,2,3]]
		);
	}
}

module 2dgraph(bounds=[-10,10], th=2, steps=10, polar=false, parametric=false) {
	step = (bounds[1]-bounds[0])/steps;
	union() {
		for(i = [bounds[0]:step:bounds[1]-step]) {
			if(polar) {
				nextPolygon(polarX(i), polarY(i), polarX(i+step), polarY(i+step), polarX(i+2*step), polarY(i+2*step), th);
			}
			else if(parametric) {
				nextPolygon(x(i), y(i), x(i+step), y(i+step), x(i+2*step), y(i+2*step), th);
			}
			else {
				nextPolygon(i, f(i), i+step, f(i+step), i+2*step, f(i+2*step), th);
			}
		}
	}
}
