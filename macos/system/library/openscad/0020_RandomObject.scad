// [FL_INDEX: keywords="openscad, 3d_parametric, RandomObject, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: RandomObject


seed=12;
$fn=50;

random_vect=rands(0,100,22);
random_style=rands(0,1,2);
random_deg=rands(0,360,2);
random_height=rands(0,200,2);
random_translate=rands(-50,50,3);


echo( "random_vect ",random_vect);
echo("random_deg ", random_deg[1]);
echo("random_height ", random_height[1]);
echo("random_translate ", random_translate[1], " ; ",random_translate[2]);


if(round(random_style[1]) == 1){
	echo( "Random Style: line");
	linear_extrude(height = random_height[1], center = true, twist = random_deg[1])
		translate([random_translate[1],random_translate[2],0])
		translate([-50,-50,0])
			shape();
}else{
	echo( "Random Style: rotate");
	rotate_extrude(convexity = 10)
		translate([random_translate[1],random_translate[2],0])
		translate([-50,-50,0])
			shape();
}



module shape(){
polygon(points=[
[random_vect[1],random_vect[2]]
,[random_vect[2],random_vect[3]]
,[random_vect[3],random_vect[4]]
,[random_vect[4],random_vect[5]]
]
, paths=[[0,1,2,3]]);


polygon(points=[
[random_vect[5],random_vect[6]]
,[random_vect[6],random_vect[7]]
,[random_vect[7],random_vect[8]]
,[random_vect[8],random_vect[9]]
]
, paths=[[0,1,2,3]]);


polygon(points=[
[random_vect[9],random_vect[10]]
,[random_vect[10],random_vect[11]]
,[random_vect[11],random_vect[12]]
,[random_vect[12],random_vect[13]]
]
, paths=[[0,1,2,3]]);


polygon(points=[
[random_vect[13],random_vect[14]]
,[random_vect[14],random_vect[15]]
,[random_vect[15],random_vect[16]]
,[random_vect[16],random_vect[17]]
]
, paths=[[0,1,2,3]]);


polygon(points=[
[random_vect[17],random_vect[18]]
,[random_vect[18],random_vect[19]]
,[random_vect[19],random_vect[20]]
,[random_vect[20],random_vect[21]]
]
, paths=[[0,1,2,3]]);
}