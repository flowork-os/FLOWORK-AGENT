# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_hand_saw_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of hand saw in Blender code

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

metal_material = bpy.data.materials.new(name="Metal")
metal_material.diffuse_color = (0.5, 0.5, 0.5, 1)
wood_material = bpy.data.materials.new(name="Wood")
wood_material.diffuse_color = (0.8, 0.4, 0.1, 1)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
blade_object = bpy.context.object
blade_object.name = "Blade"
blade_object.scale[0] = 3
blade_object.scale[1] = 0.05
blade_object.scale[2] = 0.5
blade_object.data.materials.append(metal_material)

for tooth_index in range(12):
    tooth_loc = (-2.7 + tooth_index * 0.5, 0, -0.5)
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.1, depth=0.2, location=tooth_loc)
    tooth_item = bpy.context.object
    tooth_item.name = f"Tooth {tooth_index + 1}"
    tooth_item.rotation_euler[1] = math.pi / 2
    tooth_item.data.materials.append(metal_material)

bpy.ops.mesh.primitive_cube_add(size=1, location=(3.5, 0, 0))
handle_object = bpy.context.object
handle_object.name = "Handle"
handle_object.scale[0] = 0.5
handle_object.scale[1] = 0.3
handle_object.scale[2] = 1
handle_object.data.materials.append(wood_material)

for grip_offset in [0.2, -0.2]:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=1, location=(3.5, grip_offset, 0.5), rotation=(0, math.pi / 2, 0))
    grip_object = bpy.context.object
    grip_object.name = "Grip"
    grip_object.data.materials.append(wood_material)


# --- 3DCodeVerse geo variant: neutralize materials (auto-derived, do not edit) ---
import bpy as _bpy_geo
_geo_mat = _bpy_geo.data.materials.get("geo_neutral") or _bpy_geo.data.materials.new("geo_neutral")
try:
    _geo_mat.use_nodes = False
except Exception:
    pass
try:
    _geo_mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)
except Exception:
    pass
for _geo_obj in list(_bpy_geo.data.objects):
    if _geo_obj.type == "MESH" and _geo_obj.data is not None:
        try:
            _geo_obj.data.materials.clear()
            _geo_obj.data.materials.append(_geo_mat)
        except Exception:
            pass
# --- end geo variant ---
