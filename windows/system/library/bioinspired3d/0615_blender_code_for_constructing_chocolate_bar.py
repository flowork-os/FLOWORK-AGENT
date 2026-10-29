# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_constructing_chocolate_bar" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for constructing chocolate bar.

import bpy

# Clear all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material representing dark chocolate
chocolate_material = bpy.data.materials.new(name='Dark Chocolate')
chocolate_material.diffuse_color = (0.24, 0.15, 0.10, 1)

# Create the main body of the chocolate bar
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
base_cube = bpy.context.object
base_cube.name = 'Chocolate Body'
base_cube.scale = (1, 0.5, 0.1)
base_cube.data.materials.append(chocolate_material)

# Function to create segments of the chocolate bar

def create_segment(x_pos, y_pos):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_pos, y_pos, 0.1))
    segment_cube = bpy.context.object
    segment_cube.scale = (0.2, 0.2, 0.1)
    segment_cube.data.materials.append(chocolate_material)

# Generate segments
for i in range(8):
    for j in range(4):
        x_position = (i - 4 + 0.5) * (0.2 + 0.05)
        y_position = (j - 2 + 0.5) * (0.2 + 0.05)
        create_segment(x_position, y_position)


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
