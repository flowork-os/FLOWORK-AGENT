# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_creating_a_model_of_dining_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for creating a model of dining table.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create wood material
wood_texture = bpy.data.materials.new(name='Wood Texture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

# Generate the table and legs
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
table_surface = bpy.context.object

# Adjust table dimensions
table_surface.scale[0] = 2.5  # Length
table_surface.scale[1] = 1.2  # Width
table_surface.scale[2] = 0.1  # Thickness
table_surface.name = 'Surface'
table_surface.data.materials.append(wood_texture)

# Define leg positions
leg_coordinates = [(-2.4, -1.1, 0.5), (2.4, -1.1, 0.5), (-2.4, 1.1, 0.5), (2.4, 1.1, 0.5)]

# Create each leg
for index, coord in enumerate(leg_coordinates):
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=coord)
    leg_part = bpy.context.object
    leg_part.scale[2] = 5  # Height
    leg_part.name = f'Leg Number {index + 1}'
    leg_part.data.materials.append(wood_texture)


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
