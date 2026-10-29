// [FL_INDEX: keywords="openscad, 3d_parametric, Customizable_Box, csg_solid" | COT="Parametric OpenSCAD design from 3DCodeverse"]
// Title: Customizable Box

/* [Global] */

// Part to print
part = "both"; // [first:Box only,second:Lid Only,both:Box and Lid, assembly:Assembled box]

/* [Content] */

// Size of the content in x
contentXSize = 66.0;

// Size of the content in y
contentYSize = 52.0;

// Size of the content in z
contentZSize = 19.4;

/* [Screw] */

// Use screws to secure the lid
useScrew = "first"; // [first:Yes,second:No]

// Size of the screw hole in the box
screwSize = 1.5;

// Size of the screw hole in the lid
lidScrewHoleSize = 2;

// Width of the screw head
screwHeadWidth = 3;

// Height of the screw head
screwHeadHeight = 2.6;

/* [Walls] */

// Thickness of all walls except the rim
wallThickness = 3.2;

// Height of the rim
rimHeight = 3.0;

// Thickness of the rim, should be <= wallThickness
rimThickness = wallThickness;

// Cut out the lid to print faster and save material
useThinLid = "first"; // [first:Yes,second:No]

/* [Other] */

// Tolerance for the size in x and y
tolerance = 0.5;

// Show content placeholder in pink
showContentPlaceholder = false;

/* [Hidden] */

epsilon = 0.1;

module print_part()
{
	if (part == "first")
		box();
	else if (part == "second")
		lid();
	else if (part == "both")
		both();
	else if (part == "assembly")
		assembly();
	else
		both();
}

print_part();

// The actual geometry

// Additional size needed but difficult to calculate, this is only an approximation
additionalScrewCubeSize = screwHeadHeight + screwHeadWidth;

useScrewBool = useScrew == "first" ? true : false;
useThinLidBool = useThinLid == "first" ? true : false;

screwCubeSize = useScrewBool ? screwSize + 2 * wallThickness + additionalScrewCubeSize : 0;

xSize = contentXSize + 2 * wallThickness + 2 * screwCubeSize + tolerance;
ySize = contentYSize + 2 * wallThickness + tolerance;
zSize = contentZSize + tolerance;

tx0 = wallThickness;
tx1 = wallThickness + screwCubeSize / 2;
tx2 = xSize - screwCubeSize / 2 -wallThickness;
tx3 = xSize - screwCubeSize - wallThickness;
ty0 = wallThickness;
ty1 = wallThickness + screwCubeSize / 2;
ty2 = ySize - screwCubeSize / 2 - wallThickness;
ty3 = ySize - screwCubeSize - wallThickness;
tz0 = wallThickness;
tz1 = wallThickness + epsilon;
holeheight = wallThickness + rimHeight + 2 * epsilon;

$fs=0.3;

module screwbox(x0, y0, x1, y1)
{
	difference()
	{
		translate([x0, y0, tz0]) cube([screwCubeSize, screwCubeSize, zSize]);
		translate([x1, y1, tz1]) cylinder(r = screwSize, h = zSize + epsilon);
	}
}

module box()
{
	// Base box
	translate([0, 0, 0]) cube([xSize, ySize, wallThickness]);
	translate([wallThickness, 0, wallThickness]) cube([xSize - 2 * wallThickness, wallThickness, zSize]);
	translate([wallThickness, ySize - wallThickness, wallThickness]) cube([xSize - 2 * wallThickness, wallThickness, zSize]);
	translate([0, 0, wallThickness]) cube([wallThickness, ySize, zSize]);
	translate([xSize - wallThickness, 0, wallThickness]) cube([wallThickness, ySize, zSize]);

	// Rim
	translate([0, 0, zSize + wallThickness]) cube([xSize, rimThickness, rimHeight]);
	translate([0, ySize - rimThickness, zSize + wallThickness]) cube([xSize, rimThickness, rimHeight]);
	translate([0, rimThickness, zSize + wallThickness]) cube([rimThickness, ySize - 2 * rimThickness, rimHeight]);
	translate([xSize - rimThickness, rimThickness, zSize + wallThickness]) cube([rimThickness, ySize - 2 * rimThickness, rimHeight]);

	// Screw boxes
	screwbox(tx0, ty0, tx1, ty1);
	screwbox(tx0, ty3, tx1, ty2);
	screwbox(tx3, ty0, tx2, ty1);
	screwbox(tx3, ty3, tx2, ty2);

    // Content placeholder
	if (showContentPlaceholder)
    	translate([wallThickness + screwCubeSize, wallThickness, wallThickness]) color("red") cube([contentXSize, contentYSize, contentZSize]);
}

module lidScrewHole(x, y)
{
	translate([x, y, -epsilon]) cylinder(r = lidScrewHoleSize, h = holeheight + screwHeadHeight + epsilon);
	translate([x, y, screwHeadHeight -epsilon]) cylinder(r1 = screwHeadWidth, r2 = lidScrewHoleSize, h = screwHeadHeight + epsilon);
	translate([x, y, -epsilon]) cylinder(r = screwHeadWidth, h = screwHeadHeight + epsilon);
}

module lid()
{
    lidThickness = screwHeadHeight * 3 / 2;
	difference()
	{
		union()
		{
			translate([0, 0, 0]) cube([xSize, ySize, lidThickness]);
			translate([rimThickness, rimThickness, screwHeadHeight * 3 / 2]) cube([xSize- 2 * rimThickness, ySize - 2 * rimThickness, rimHeight]);
		}

        if (useScrewBool)
        {
            lidScrewHole(tx1, ty1);
            lidScrewHole(tx1, ty2);
            lidScrewHole(tx2, ty1);
            lidScrewHole(tx2, ty2);

            if (useThinLidBool)
            {
                offset = wallThickness + screwCubeSize;
                translate([offset, wallThickness + rimThickness, lidThickness - epsilon]) cube([xSize - 2 * offset, ySize - 2 * (wallThickness + rimThickness), rimHeight + 2 * epsilon]);
                translate([wallThickness + rimThickness, offset, lidThickness - epsilon]) cube([xSize - 4 * wallThickness, ySize - 2 * offset, rimHeight + 2 * epsilon]);
            }
        }
        else if (useThinLidBool)
        {
            translate([wallThickness + rimThickness, wallThickness + rimThickness, lidThickness - epsilon]) cube([xSize - 2 * (wallThickness + rimThickness), ySize - 2 * (wallThickness + rimThickness), rimHeight + 2 * epsilon]);
        }
	}
}

module both()
{
	box();
	translate([0, ySize + 10, 0]) lid();
}

module assembly()
{
	box();
	color("red") translate([0, 0, zSize + 2 * wallThickness + rimHeight + 2 * epsilon]) mirror ([0, 0, 1]) lid();
}
