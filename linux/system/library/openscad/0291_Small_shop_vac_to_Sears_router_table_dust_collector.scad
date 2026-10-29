// [FL_INDEX: keywords="openscad, 3d_parametric, Small_shop_vac_to_Sears_router_table_dust_collector, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Small shop vac to Sears router table dust collector

// Outer diameter in millimeters - use 57 for standard hose connection for 2 1/4" shop vac
outer = 57;
// Inner diameter in millimeters - use 31.25 for the tapered connector on a 1 1/4" shop vac
inner = 31.25;
// Length of adapter in millimeters
length = 40;

difference() {
cylinder( h=length, r=outer/2, center=false, $fn=144 );
cylinder( h=length, r=inner/2, center=false, $fn=144 );
}
