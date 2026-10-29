# [FL_INDEX: keywords="blender_factory, procedural_3d, DustMoteFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: DustMoteFactory | Category: factories_geo
# Prompt: A 3D model of a dust mote particle rendered from a slightly elevated perspective, featuring a faceted geodesic sphere shape with irregular polygonal faces and a semi-translucent pinkish-brown appearance with subtle cloudy surface detail.

import bpy

SEED = 0

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.context.scene.cursor.location = (0, 0, 0)

bpy.ops.mesh.primitive_ico_sphere_add(radius=1, subdivisions=2, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "DustMoteFactory"

