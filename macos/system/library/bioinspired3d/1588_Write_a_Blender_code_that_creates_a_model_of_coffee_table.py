# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_code_that_creates_a_model_of_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender code that creates a model of coffee table.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set up material for the table
wood_texture = bpy.data.materials.new(name='WoodTexture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)  # Define wood color

# Create the tabletop
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
table_surface = bpy.context.object

# Adjust dimensions of the tabletop
table_surface.name = 'Tabletop'
table_surface.scale = (2, 1, 0.1)
table_surface.data.materials.append(wood_texture)

# Define leg specifications
leg_height = 0.5
leg_radius = 0.05
leg_coords = [(-1.9, -0.9, leg_height / 2), (1.9, -0.9, leg_height / 2), (-1.9, 0.9, leg_height / 2), (1.9, 0.9, leg_height / 2)]

# Create legs using a loop
for idx, coord in enumerate(leg_coords):
    bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=leg_height, location=coord)
    leg_part = bpy.context.object
    leg_part.name = f'Leg_{idx + 1}'
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
