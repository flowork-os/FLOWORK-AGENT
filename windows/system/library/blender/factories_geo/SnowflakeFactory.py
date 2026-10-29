# [FL_INDEX: keywords="blender_factory, procedural_3d, SnowflakeFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SnowflakeFactory | Category: factories_geo
# Prompt: A 3D model of a snowflake rendered from a slightly elevated perspective, featuring a flat thin hexagonal plate shape with clean straight edges and a uniform white appearance, resembling a simple crystalline ice platelet.

import bpy

SEED = 0

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.context.scene.cursor.location = (0, 0, 0)

bpy.ops.mesh.primitive_circle_add(vertices=6, fill_type='TRIFAN', location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "SnowflakeFactory"

