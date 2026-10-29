// [FL_INDEX: keywords="openscad, 3d_parametric, Split_Heart, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Split Heart

// ===== file: heart-split-sins.scad =====
//Size of Heart shape  - long edge
Size=25;
//Height of Heart
Height= 5;
//Cut width
Cut = 0.4;
//Hole size
Hole=2;

module heart(size,height,hole) {
  linear_extrude(height = height) {
     square(size);
     translate([size/2,size,0]) 
       difference() {
             circle(size/2,$fn=50);
             translate([0,size*0.3,0]) circle(hole,$fn=50);       }
     translate([size,size/2,0])
        difference() {
             circle(size/2,$fn=50);
             translate([size*0.3,0,0]) circle(hole,$fn=50);
        }
  }
}

module path_open(height,width,path) {
    for (t = [0: len(path)-2 ])
          hull() {
            translate(path[t]) cylinder(h=height, r=width/2,center=true,$fn=4);
            translate(path[t + 1]) cylinder(h=height, r=width/2,center=true,$fn=4);
          }
};

function path(n,step,c,t=0) =
     t < n
       ? concat( [[t * step, f(t,c),0]],
                 path(n,step, c, t+1)
          )
       : []
;

function coefficients(n,a) =
      n == 0
         ? []
         : concat(rands(-a,a,1)[0],coefficients(n-1,a));

function f(t,c) =
   sin(t/2)*( c[0]* sin(t) + c[1] * sin(2*t)+ c[2]*sin(3*t) +c[3] * sin(4*t)+ 
              c[4]* sin(5*t) + c[5]* sin(7*t) + c[6]*sin(8*t)) ;


N= 181;
Step = Size * sqrt(2)/N;
c=coefficients(7,Size/6);
echo(c);

cut_path = path(N,Step,c);

echo(cut_path);
// path_open(Height,Cut,cut_path);

difference() {
    heart(Size,Height,Hole);
    translate ([0,0,Height/2])
       rotate([0,0,45]) 
         path_open(Height,Cut,cut_path);
}


// ===== file: heart-split.scad =====
//Size of Heart shape  - long edge
Size=25;
//Height of Heart
Height= 5;
// N - segments in cut
N = 12;
//Cut width
Cut = 0.5;
//Hole size
Hole=2;

module heart(size,height,hole) {
  linear_extrude(height = height) {
     square(size);
     translate([size/2,size,0]) 
       difference() {
             circle(size/2);
             translate([0,size*0.3,0]) circle(hole);       }
     translate([size,size/2,0])
        difference() {
             circle(size/2);
             translate([size*0.3,0,0]) circle(hole);
        }
  }
}

module path_open(height,width,path) {
    for (t = [0: len(path)-2 ])
          hull() {
            translate(path[t]) cylinder(h=height, r=width/2,center=true);
            translate(path[t + 1]) cylinder(h=height, r=width/2,center=true);
          }
};

function y_step(current_y, limit, amplitude) =
     current_y > limit 
       ?  - rands(0,amplitude,1)[0]
       :  current_y < - limit
           ?  rands(0,amplitude,1)[0]
           :  rands(-amplitude, amplitude,1)[0]
;

function path(n, point, step, limit, amplitude) =
     n == 0
       ? [[point[0],0,0]]
       : concat([point],
            path(n-1, 
                 point + [step, y_step(point[1], limit, amplitude),0 ],
                 step,limit,amplitude)
         )
;

$fn=40;
Step = Size * sqrt(2) /N;

// cut shape controls
A = 1.5;  // corridor 
B = 1.5;  // Amplitude 
limit = Step * A;   
amplitude = Step * B;  

//echo (Step, limit, amplitude);
cut_path = concat([[0,0,0]],path(N-1,[Step,0,0], Step, limit, amplitude));

// echo(cut_path);
difference() {
    heart(Size,Height,Hole);
    translate ([0,0,Height/2])
       rotate([0,0,45]) 
         path_open(Height,Cut,cut_path);
}
