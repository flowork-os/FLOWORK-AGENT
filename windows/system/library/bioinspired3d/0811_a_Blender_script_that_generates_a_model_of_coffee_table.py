# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_that_generates_a_model_of_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script that generates a model of coffee table.

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize wood material
wood_texture = bpy.data.materials.new(name='Wood Texture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)  # Wood-like color

# Create the tabletop as a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
table = bpy.context.object
table.scale = (2, 1, 0.1)
table.name = 'Tabletop'
table.data.materials.append(wood_texture)

# Define parameters for the legs
height_of_legs = 1
radius_of_legs = 0.05
positions_of_legs = [(-1.9, -0.9, height_of_legs / 2), (1.9, -0.9, height_of_legs / 2), (-1.9, 0.9, height_of_legs / 2), (1.9, 0.9, height_of_legs / 2)]

# Function to add legs
for idx, pos in enumerate(positions_of_legs):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_legs, depth=height_of_legs, location=pos)
    leg_obj = bpy.context.object
    leg_obj.name = f'Leg_{idx + 1}'
    leg_obj.data.materials.append(wood_texture)

# Create the lower shelf
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
shelf_object = bpy.context.object
shelf_object.scale = (2, 1, 0.05)
shelf_object.name = 'Lower Shelf'
shelf_object.data.materials.append(wood_texture)


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
