# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_coffee_table_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create coffee table using blender script

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Setup a material for the table
material_wood = bpy.data.materials.new(name='WoodTexture')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)  # Wood-like color

# Create the table top
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
table_surface = bpy.context.object

table_surface.scale = (2, 1, 0.1)  # Set dimensions for the table top

table_surface.name = 'TableSurface'
table_surface.data.materials.append(material_wood)

# Define leg parameters
height = 0.5
radius = 0.05
legs = [(-1.9, -0.9, height / 2), (1.9, -0.9, height / 2), (-1.9, 0.9, height / 2), (1.9, 0.9, height / 2)]

# Create legs using a loop
for index, leg_position in enumerate(legs):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=leg_position)
    leg = bpy.context.object
    leg.name = f'Leg_{index + 1}'
    leg.data.materials.append(material_wood)


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
