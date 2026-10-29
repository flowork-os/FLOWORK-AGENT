// [FL_INDEX: keywords="openscad, 3d_parametric, Collar_Stay_Box_Customizer, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Collar Stay Box Customizer

// holder for collar stays
$fn=50*1;

//How wide should the box be (mm)?
wt = 100; //[24:250]
w=wt-6;

//How deep should the box be (mm)?
dt = 60; //[16:250]
d=dt-6;

//How many slots across width?
hw = floor((w)/17);

//Gap size on end
gw = (w-(hw-1)*17)/2;

//How many slots across depth
hd = floor((d)/10);

//Gap size on end
gd = (d-(hd-1)*10)/2;
echo (gd);

difference() {
	minkowski(){
		cube([w,d,29]);
		cylinder (r=3,h=1);
	}
	for (i = [0:hw-1]) {
		for (j = [0:hd-1]) {
			translate([gw+i*17-7,gd+j*10-1,5]) cube([14,2,29]);
		}
      }
}

