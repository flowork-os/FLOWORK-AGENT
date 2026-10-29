// [FL_INDEX: keywords="openscad, 3d_parametric, Euro_shopping_cart_token__with_carabiner, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Euro shopping cart token, with carabiner

// Carabinier parameters

// Coin parameters
// Thickness of the coin (2.33 for 1 EURO)
HCOIN=2.33;

// Radius of the coin (11.625 for 1 EURO)
DCOIN=11.625;

// Internal radius, ie radius of the thinner part. Arbitrary
DICOIN=10;

// Thickness of the inside. 1mm is strong enough, and let space for visible motif. 
THCOIN=1; 

// Dimensions of carabiner. Play with to understand each one role.
L1=8;

// Radius
R=8;

// Angle
A=40;

// Length
L2=10;

// Number of circonvolution of the flexible part. 0 for straight flexible part (not advised)
NL=3;

// Thickness of the flexible part
TH=0.8;

// Text part
// Text
YOURTEXT="Coin";

// X offset for text. Should be 0, unless you use some weird unicode
TEXT_OFFSETX=0;

// Y offset for text
TEXT_OFFSETY=0;

// scale factor for text width. Should be 1, unless you use some weird unicode
TEXT_SCALEX=1;

// scale factor for text height
TEXT_SCALEY=1;

VERSION=6;

// Logo file. Does not work with Thingiverse customizer.
// YOURLOGOFILE="propositionNewLogo.dxf";

// Scale and center the logo if needed
//LOGOX=-16; // Scale and center the logo
//LOGOY=-5;
//LOGOW=16;

// === End of parameters =================================================


/*
if ((!YOURTEXT || YOURTEXT=="") && YOURLOGOFILE) {
// Attempt to automatically resize logo. It will not fit exactly, but at least your logo should not be 1000 times smaller or larger than the coin. Adjust with LOGOX/Y/W
    translate([LOGOX,LOGOY,1]) resize([0,0,HCOIN-THCOIN]) resize([LOGOW,0,0], auto=true) scale([0.01, 0.01, 1]) linear_extrude(HCOIN-THCOIN) import(YOURLOGOFILE); // scale+resize is strange, I know. This is to bypass a bug in OpenScad 2013.06. This bug is documented and should be removed in next release of OpenScad
}
*/

if(YOURTEXT && YOURTEXT!=""){
   translate([-DICOIN*((len(YOURTEXT)==1)?1:0.8)+TEXT_OFFSETX, -DICOIN/2+TEXT_OFFSETY+1, 0]) resize([DICOIN*1.5*TEXT_SCALEX, DICOIN*0.9*TEXT_SCALEY, HCOIN]) linear_extrude(HCOIN) text(YOURTEXT);
}


// The coin
difference(){
   cylinder(h=HCOIN, r=DCOIN, $fn=100);
   translate([0, 0, THCOIN]) cylinder(h=HCOIN, r=DICOIN, $fn=100);
}

// First part of the hook. Straight part starting from coin of length L1
translate([-HCOIN/2, DCOIN-0.125, 0]) cube([HCOIN, L1, HCOIN]);


// Second part (turning in trigonometric direction) of the hook. A straight line at angle A
xbgoblique = -cos(A)*HCOIN/2;
ybgoblique = DCOIN-0.125+L1-HCOIN*0.5*cos(A)/sin(A)-HCOIN*0.5*cos(A)*cos(A)/sin(A);
lbgoblique = (R+xbgoblique)/sin(A);
translate([xbgoblique, ybgoblique ,0]) rotate(a=-A,v=[0,0,1]) cube([HCOIN,lbgoblique,HCOIN]);


// 3r part (vertical)
ybdoblique=ybgoblique-sin(A)*HCOIN;
yhdoblique=ybdoblique+cos(A)*lbgoblique;
translate([R-HCOIN,yhdoblique,0]) cube([HCOIN,L2,HCOIN]);


// 4th part (half a circle and a hosting part for flexible part)
translate([0, yhdoblique+L2, 0]) difference(){
   cylinder(h=HCOIN, r=R, $fn=40);
   translate([0,0,-1]) cylinder(h=HCOIN+2, r=R-HCOIN, $fn=40);
   translate([-25, -50-0.375*R, -25]) cube([50,50,50]);
   translate([0,-50,-25]) cube([50,50,50]);
   translate([-R+HCOIN+0.8,-0.375*R+HCOIN/2,HCOIN/2]) rotate([0,0,20]) rotate([90,0,0]) rotate([0,0,45]) color("red") cube([HCOIN, HCOIN, 3], center=true);
}


// 5th part, the flexible one
// Length of the flexible part
hress=yhdoblique+L2-DCOIN+0.125-L1-0.375*R-4.5;
lress=sqrt(R*R+hress*hress);

// One loop (has to be scaled par caller)
module oneloop(){
	difference(){
	   cylinder(h=HCOIN, r=1.3, $fn=10);
		translate([0,0,-0.01]) cylinder(h=HCOIN+0.02, r=1.3-TH, $fn=10);
		translate([0, -5, -0.01]) cube([10,10,HCOIN+0.02]);
	}
}

// A pair of them, linked together
module chain(){
	translate([-0.6, 0,0]) oneloop();
    translate([0.6, 2.6-TH, 0]) mirror([1,0,0]) oneloop();
	translate([-0.6,1.3-TH,0]) cube([1.2, TH, HCOIN]);
	translate([-0.6,3.9-2*TH,0]) cube([1.2, TH, HCOIN]);
}
LL=5.2-2*TH;

// A sequence of those, make a flexible part
module chaine(n){
   for(i=[0:1:n]) translate([0, LL*i,0]) chain();
}

// That "chaine" module has a fixed length of 3.6*NL. Caller must scale it to give if the wanted length

// End of the flexible part
module finress(){
	translate([-1.8,0,0]) cube([HCOIN,HCOIN,HCOIN]);
	translate([-0.5,0,0]) cube([1,4.5, HCOIN]);
	translate([-1.5,0,0]) rotate(a=-90, v=[1,0,0]) linear_extrude(4.5) polygon([[0,-HCOIN/2], [1,-HCOIN], [1,0]]);
}


translate([0, DCOIN-0.125+L1+0.7, 0]) rotate(a=40, v=[0,0,1]) scale([lress/NL/LL, lress/NL/LL, 1]) {
	chaine(NL-1);
	translate([0,NL*LL-1.3, 0]) scale([NL*LL/lress, NL*LL/lress, 1]) finress();
}