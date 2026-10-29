# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_that_creates_a_model_of_geometric_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code that creates a model of geometric pattern.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize a material for the shapes
material_for_shapes = bpy.data.materials.new(name='Shape Color')
material_for_shapes.diffuse_color = (0.2, 0.2, 0.8, 1)  # Blue color

# Create a function to add a triangle

def add_triangle(i, j):
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=1, depth=0.1, location=(i, j, 0))
    current_triangle = bpy.context.object
    current_triangle.name = f'Triangle_{i}_{j}'
    current_triangle.data.materials.append(material_for_shapes)

# Loop to create a grid
for i in range(10):
    for j in range(10):
        add_triangle(i, j)


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
