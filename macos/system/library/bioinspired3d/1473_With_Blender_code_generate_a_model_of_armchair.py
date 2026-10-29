# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_Blender_code_generate_a_model_of_armchair" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With Blender code generate a model of armchair

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)
cushion_material = bpy.data.materials.new(name='CushionMaterial')
cushion_material.diffuse_color = (0.8, 0.4, 0.4, 1)

# Function to create a leg

def create_leg(index, x_offset, y_offset):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.0, location=(x_offset, y_offset, -0.5))
    leg_object = bpy.context.object
    leg_object.name = f'Leg_{index}'
    leg_object.data.materials.append(wood_material)

# Generate the legs
for i in range(4):
    x_position = 0.6 * (i % 2) - 0.3
    y_position = 0.6 * (i // 2) - 0.3
    create_leg(i + 1, x_position, y_position)

# Create the seat
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0, 0, 0.1))
seat_object = bpy.context.object
seat_object.name = 'Seat'
seat_object.scale = (1, 1, 0.2)
seat_object.data.materials.append(cushion_material)

# Create the backrest
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0, -0.55, 0.75))
backrest_object = bpy.context.object
backrest_object.name = 'Backrest'
backrest_object.scale = (1, 0.1, 1.5)
backrest_object.data.materials.append(wood_material)

# Function to create an armrest

def create_armrest(index, x_position):
    bpy.ops.mesh.primitive_cube_add(size=1.2, location=(x_position, 0, 0.5))
    armrest_object = bpy.context.object
    armrest_object.name = f'Armrest_{index}'
    armrest_object.scale = (0.1, 1, 0.2)
    armrest_object.data.materials.append(wood_material)

# Generate the armrests
for j in range(2):
    create_armrest(j + 1, 0.55 * (j * 2 - 1))


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
