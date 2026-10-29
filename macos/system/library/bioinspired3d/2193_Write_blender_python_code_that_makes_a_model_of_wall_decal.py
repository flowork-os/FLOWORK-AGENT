# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_python_code_that_makes_a_model_of_wall_decal" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender python code that makes a model of wall decal

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the wall with specified color
material_wall = bpy.data.materials.new(name='Wall Color')
material_wall.diffuse_color = (0.8, 0.8, 0.8, 1)

# Create the base plane representing the wall
bpy.ops.mesh.primitive_plane_add(size=5, location=(0, 0, 0))
wall_base = bpy.context.object
wall_base.name = 'Base Wall'
wall_base.data.materials.append(material_wall)

# Define a material for the squares with a different color
material_square = bpy.data.materials.new(name='Square Shade')
material_square.diffuse_color = (0.2, 0.2, 0.2, 1)

# Helper function to create squares
def generate_square(x_coordinate, y_coordinate):
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(x_coordinate, y_coordinate, 0.01))
    square_created = bpy.context.object
    square_created.name = f'Square_{x_coordinate+3}_{y_coordinate+3}'
    square_created.data.materials.append(material_square)

# Loop to create a grid of squares
for x in range(-2, 3):
    for y in range(-2, 3):
        generate_square(x, y)


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
