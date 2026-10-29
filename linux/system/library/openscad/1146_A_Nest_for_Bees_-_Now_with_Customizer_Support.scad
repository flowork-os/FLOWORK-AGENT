// [FL_INDEX: keywords="openscad, 3d_parametric, A_Nest_for_Bees_-_Now_with_Customizer_Support, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: A Nest for Bees - Now with Customizer Support!

 /*!
@brief A Nest for Bees
@details This OpenSCAD script will generate a simple multi unit Bpartment to hold your Bees

@author Mark Gaffney
@version 0.4
@date 2013-03-19

@todo
Fill with Bees!

@warning
Bees should not be disturbed willy nilly!

@note
Changes from previous versions:
0.4
 - renamed some varaibles to make more easy to use with "MakerBot's Thingiverse Customizer"
 - fixed some alignment issues with hexagons
 - fixed off by 1 error for rows and columns
 - fixed some manifoldness issues with cutouts
0.3
 - fixed up some translates to properly account for the chosen wall thickness
 - added option to make hexagons...but it's not very pretty
0.2
 - added union command so all the cells are joined as one solid piece
0.1
 - First implementation

@attention
Copyright (c) 2013 Tyndall National Institute.
All rights reserved.
Permission to use, copy, modify, and distribute this software and its documentation for any purpose, without fee, and without written agreement is hereby granted, provided that the above copyright notice and the following two paragraphs appear in all copies of this software. 

IN NO EVENT SHALL TYNDALL NATIONAL INSTITUTE BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF TYNDALL NATIONAL INSTITUTE HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

TYNDALL NATIONAL INSTITUTE SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.  THE SOFTWARE PROVIDED HEREUNDER IS ON AN "AS IS" BASIS, AND TYNDALL NATIONAL INSTITUTE HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.
*/


//**************User*Variables*****************
//these values are all in millimetres... of course! Change them to suit your printer and bee population!

/* [Bpartment Size and Shape] */
// Height: How long a tunnel does your bee like?
height=40;//[20:100]
//Inner Diameter: How wide is your bee?
inner_d=9;// [5:40]
// Wall Thickness: How thin a wall call your printer produce?
wall_t=2;//[0.1:5]
// Row Count: How many floors in this Bpartment?
rows=2;//[1:10]
// Column Count: How many Bpartments per floor?
columns=4;//[1:10]
//Hexagons or Circles: What shape is each Bpartment?
use_hexagons=1;//[0:circle, 1:hexagon]
//If hexagons appear not to mesh nicely try using this
fix=0;//[0:1]

//*********************Calls*******************
/* [Hidden] */
a_bit=0.1;
$fn=6*use_hexagons;//if using circles get 0 which causes OpenSCAD to use the default value instead

union(){

translate(v=[wall_t+(inner_d/2),wall_t+(inner_d/2),height/2]){
	for (i=[0:columns-1]){
		translate (v=[i*(inner_d+(wall_t/2)) -(wall_t/2)*i*use_hexagons,(i%2)*((wall_t+inner_d)/2 -use_hexagons*0.0*wall_t ),0]){
			for (j=[0:rows-1]){
				translate (v=[0,j*(inner_d+wall_t)-j*use_hexagons*0.8*wall_t,0]){
					difference(){
						rotate(a=30*use_hexagons*fix, v=[0,0,1]) cylinder(h=height, r=(inner_d/2)+wall_t+wall_t*use_hexagons*0.15, center=true);
						rotate(a=30*use_hexagons*fix, v=[0,0,1]) cylinder(h=height+2*a_bit, r=(inner_d/2), center=true);
					}
				}
			}
		}
	}
}


}