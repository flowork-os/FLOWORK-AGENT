# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_script_to_create_a_model_of_quilt" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender script to create a model of quilt.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the cubes
material_a = bpy.data.materials.new(name='MaterialA')
material_a.diffuse_color = (0.8, 0.2, 0.2, 1)
material_b = bpy.data.materials.new(name='MaterialB')
material_b.diffuse_color = (0.2, 0.8, 0.2, 1)

# Function to generate a cube with a material
def generate_cube(x_pos, y_pos, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_pos, y_pos, 0))
    current_cube = bpy.context.object
    current_cube.name = f'Cube_{x_pos}_{y_pos}'
    current_cube.data.materials.append(mat)

# Loop to create a checkerboard pattern of cubes
for i in range(5):
    for j in range(5):
        generate_cube(i, j, material_a if (i + j) % 2 == 0 else material_b)


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
