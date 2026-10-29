// [FL_INDEX: keywords="openscad, 3d_parametric, Simple_S_Hook_V2, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Simple S Hook V2

/*Simple S Hook by Mike Thomnpson 24/12/2023
Revision 2.0 with improved strength and customization*/

/* [Radius] */
//Profile radius - increase for heavier loads along with increased perimeters, top and bottom layers when printing
profile_radius = 5; 
//Top Radius - size of top section measured from centre of circle to centre of material
top_radius = 20;
//Bottom radius - size of bottom section measured from centre of circle to centre of material
bottom_radius = 20;

/* [Closure Angle] */
//Top closure angle - increase for tighter gap
top_closure_angle = 240;
//Bottom closure angle - increase for tighter gap
bottom_closure_angle = 240;

/* [Connector Length] */
//Connector length - adjust for extended gap between top and bottom of hook
connector_length = 15;

/* [Hidden] */
$fn=64;

top();
connector();
bottom();
//oval_profile();

module hex_profile()
{
    $fn=6;
    circle(r=profile_radius);
}

//experimental - not currently used
module oval_profile()
{ 
    oval_height =10; //y axis
    oval_depth = 10; //x axis
    polygon(points=[[-oval_depth/2,-oval_height/2],[oval_depth/2-2,-oval_height/2],[oval_depth/2,-oval_height/2+2],[oval_depth/2,oval_height/2-2],[oval_depth/2-2,oval_height/2],[-oval_depth/2+2,oval_height/2],[-oval_depth/2,oval_height/2-2],[-oval_depth/2,-oval_height/2+2],[-oval_depth/2+2,-oval_height/2]]);
}

module top()
{
    rotate_extrude(angle=top_closure_angle,convexity = 10)translate([top_radius, 0, 0])hex_profile();
    end_cap_top();
}

module bottom()
{
    translate([top_radius*2-(top_radius-bottom_radius),-connector_length,0])rotate([0,0,180])
    {
        rotate_extrude(angle=bottom_closure_angle,convexity = 10)translate([bottom_radius, 0, 0])hex_profile();
        end_cap_bottom();
    }
}

module connector()
{
    translate([top_radius,0,0])rotate([90,0,0])linear_extrude(connector_length, convexity = 10)hex_profile();
}

module end_cap_top()
{
    $fn=6;
    rotate([0,0,top_closure_angle])translate([top_radius,0,0])rotate([-90,0,0])cylinder(r1=profile_radius,r2=profile_radius-2,h=2);
}

module end_cap_bottom()
{
    $fn=6;
    rotate([0,0,bottom_closure_angle])translate([bottom_radius,0,0])rotate([-90,0,0])cylinder(r1=profile_radius,r2=profile_radius-2,h=2);
}