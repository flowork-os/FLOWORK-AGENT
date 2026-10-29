// [FL_INDEX: keywords="openscad, 3d_parametric, Schoolstuff, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Schoolstuff

// ===== file: schoolstuff-pencil-topper.scad =====
// 2013 Lukas Süss aka mechadense
// Simple Pencil Topper CC-BY

/*
I suggest printing the pencil topper layered color red black green
or printing in white and coloring manual
signal
yes or no
good mood or bad mood
*/

//outermost pencil diameter
dpencil = 7;

// outer diameter
d1 = 18;
h1 = dpencil+2;

d2 = d1/22*19;
h2 = h1*1.33;




$fa = 5*1;
$fs = 0.2*1;

through = false;

difference()
{
  hull()
  {
    cylinder(r=d1/2,h=h1,center=true);
    cylinder(r=d2/2,h=h2,center=true);
  }
  //cut pencil inlet
  rotate(90,[0,1,0])
    cylinder(r=dpencil/2,h=d1*2,center=through);

  translate([0,0,h2/2-1])
  scale([d1/19,d1/19,1])
  smileygood();

  scale([1,1,-1])
  translate([0,0,h2/2-1])
  scale([d1/19,d1/19,1])
  smileybad();

  translate([0,-d1/2-dpencil/2*1.618,0])
    rotate(90,[0,1,0])
    cylinder(r=dpencil,h=2*d1,center=true);
  translate([0,-(-d1/2-dpencil/2*1.618),0])
    rotate(90,[0,1,0])
    cylinder(r=dpencil,h=2*d1,center=true);
}

//smiley();


module smileygood()
{
  a = 3.1;
  b = 3.0;

  n = 7;
  c = 5;
  rm = 1.25;
  translate([-b,-a,0])
    cylinder(r=2,h=20,center=false);
  translate([-b,+a,0])
    cylinder(r=2,h=20,center=false);

  for(i=[-n:n])
  { 
    rotate(360/(2*n-1)*i*0.275,[0,0,1])
      translate([+c,0,0]) cylinder(r=rm,h=20,center=false);
  }
}

module smileybad()
{
  a = 3.1;
  b = 3.0;

  n = 7;
  c = 5;
  rm = 1.25;
  translate([-b,-a,0])
    cylinder(r=2,h=20,center=false);
  translate([-b,+a,0])
    cylinder(r=2,h=20,center=false);

  translate([6.75,0,0])
  for(i=[-n:n])
  { 
    rotate(180+360/(2*n-1)*i*0.275,[0,0,1])
      translate([+c,0,0]) cylinder(r=rm,h=20,center=false);
  }
}

// ===== file: schoolstuff-pencilcase.scad =====
// 2013 Lukas Süss aka mechadense CC-BY
// schoolstuff - pencilcase

/*
print the box like a vase
you need an extending and a shrinking part
they'll friction fit together.
*/


// roughly the main diameter
d0 = 50;
// height of one halve
h0 = 125; 

// height resolution
dh = 1;
$fs = dh;
$fa = 360/(d0*3.1415/dh);

// wall thickness 
t = 1;
// amplitude
a = 0.2;
// period
p = 6;
n = h0/dh;

part = "extending"; // [extending,shrinking]

// how much maximum overlap do you want to allow when sticking the two halves together 
overlapfactor = 0.33;

// the slant could be decoupled from the wallthickness
function rr1(h) = d0/2 + a*cos(h/p*360) + h/h0*t;
function rr2(h) = d0/2 + a*cos(h/p*360) - h/h0*t + t*(1-overlapfactor);


//###################
shrinkingpart();
//extendingpart();


module demo()
{
  translate([-d0/2*1.2,0,0])
    //shrinkingpart();
  translate([+d0/2*1.2,0,0])
    extendingpart();
}

module extendingpart()
{
  translate([0,0,-2]) slice(rr1(0)-2,rr1(0),2);
  for(i=[0:n-1])
  {
    translate([0,0,i*dh])
    slice(rr1(i*dh),rr1((i+1)*dh),dh);
  }
}

module shrinkingpart()
{
  translate([0,0,-2]) slice(rr2(0)-2,rr2(0),2);
  for(i=[0:n-1])
  {
    translate([0,0,i*dh])
    slice(rr2(i*dh),rr2((i+1)*dh),dh);
  }
}


module slice(r1,r2,hh)
{
  cylinder(r1=r1,r2=r2,h=hh);
}


module oldslice(r1,r2,hh)
{
  hull()
  {
    cylinder(r=r1,h=0.1);
    translate([0,0,hh]) cylinder(r=r2,h=0.1);
    //echo(rr(i*dh));
  }
}

// ===== file: shoolstuff-ruler.scad =====
// Ruler
// Lukas Süss aka mechadense 2013 CC-BY

/*

objectives:

* good functionality
* no sharp edges
* sturdiness
* minimal use of material

*/

$fa = 5;
$fs = 0.2;$

// Ruler Length
l = 160;
// glue plane width
w1 = 16;
// scaffold plane width
w2 = 16;
// blade thickness
h1 = 1.5; 
// ruler thickness
h2 = 4;

dt = 0.75; // stopper

// truss rimm thickness
a = 2.0;
s = (w2-2*a)/sqrt(2);
n = ceil(l/w2/2);

difference()
{
  union()
  {
    hull()
    {
      translate([0,(w1+w2)/2,h1/2])
        cube([l,(w1+w2),h1],center=true);
      translate([0,w2/2,h2/2])
         cube([l,w2,h2],center=true);
    }

    difference()
    {
      hull()
      {
        translate([0,(w1+w2)/2,(h1+dt)/2])
          //cube([l,(w1+w2),h1],center=true);
          oval(l,(w1+w2),h1+dt);
        translate([0,w2/2,(h2+dt*1)/2])
          //cube([l,w2,h2+dt],center=true);
          oval(l,w2,h2+dt*1);
      }
      cube([l,(w1+w2)*4,h2*3],center=true);
    }

  }

  intersection()
  {
    for(i=[-n:n])
    {
      translate([w2*i,w2/2,0])
      {
        rotate(45,[0,0,1])
        cube([s,s,3*h2],center=true);
        translate([w2/2,w2/2,0])
        rotate(45,[0,0,1])
        cube([s,s,3*h2],center=true);
        translate([w2/2,-w2/2,0])
        rotate(45,[0,0,1])
        cube([s,s,3*h2],center=true);
      }
    }
    translate([0,w2/2,h2/2])
      cube([l-10,w2-2*a,h2*3],center=true);
  }
  
}

module oval(x,y,z)
{
  union()
  {
    cube([x,y,z],center=true);
    translate([-x/2,0,0])
      cylinder(r=y/2,h=z,center=true);
    translate([+x/2,0,0])
      cylinder(r=y/2,h=z,center=true);
  }

}