# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_code_to_create_a_model_of_armchair" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender code to create a model of armchair

import bpy
import math

# Remove all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
material_wood = bpy.data.materials.new(name='MaterialWood')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)
material_cushion = bpy.data.materials.new(name='MaterialCushion')
material_cushion.diffuse_color = (0.8, 0.4, 0.4, 1)

# Create legs using a loop
for leg_index in range(4):
    leg_x = 0.6 * (leg_index % 2) - 0.3
    leg_y = 0.6 * (leg_index // 2) - 0.3
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.0, location=(leg_x, leg_y, -0.5))
    leg = bpy.context.object
    leg.name = f'Leg_{leg_index + 1}'
    leg.data.materials.append(material_wood)

# Create the seat
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0, 0, 0.1))
seat_object = bpy.context.object
seat_object.name = 'Seat'
seat_object.scale = (1, 1, 0.2)
seat_object.data.materials.append(material_cushion)

# Add the backrest
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0, -0.55, 0.75))
backrest_object = bpy.context.object
backrest_object.name = 'Backrest'
backrest_object.scale = (1, 0.1, 1.5)
backrest_object.data.materials.append(material_wood)

# Create armrests
for arm_index in range(2):
    arm_x = 0.55 * (arm_index * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=1.2, location=(arm_x, 0, 0.5))
    armrest = bpy.context.object
    armrest.name = f'Armrest_{arm_index + 1}'
    armrest.scale = (0.1, 1, 0.2)
    armrest.data.materials.append(material_wood)


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
