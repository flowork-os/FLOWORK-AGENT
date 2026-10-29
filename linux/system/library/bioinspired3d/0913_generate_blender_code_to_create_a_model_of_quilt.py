# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_code_to_create_a_model_of_quilt" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender code to create a model of quilt.

import bpy

# Clear the current Blender scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the cubes
red_material = bpy.data.materials.new(name='RedMaterial')
red_material.diffuse_color = (0.8, 0.2, 0.2, 1)
green_material = bpy.data.materials.new(name='GreenMaterial')
green_material.diffuse_color = (0.2, 0.8, 0.2, 1)

# Function to create a cube at a specific position with a material

def create_colored_cube(x, y, color):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0))
    cube = bpy.context.object
    cube.data.materials.append(color)
    cube.name = f'Cube_{x}_{y}'

# Generate a grid of cubes
for row in range(5):
    for column in range(5):
        if (row + column) % 2 == 0:
            create_colored_cube(row, column, red_material)
        else:
            create_colored_cube(row, column, green_material)


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
