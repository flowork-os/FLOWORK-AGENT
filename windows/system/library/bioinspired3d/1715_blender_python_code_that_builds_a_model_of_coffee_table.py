# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_builds_a_model_of_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that builds a model of coffee table

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definition for the table
material_wood = bpy.data.materials.new(name='Table Wood')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to add a cube for the table top
def add_table_top():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.45))
    top_surface = bpy.context.object
    top_surface.scale = (1.5, 0.75, 0.1)
    top_surface.name = 'Table Top'
    top_surface.data.materials.append(material_wood)

# Function to add legs to the table
def add_table_legs():
    height = 0.45
    radius = 0.05
    positions = [(-1.4, -0.7, height / 2), (1.4, -0.7, height / 2), (-1.4, 0.7, height / 2), (1.4, 0.7, height / 2)]
    for index, position in enumerate(positions):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
        leg = bpy.context.object
        leg.name = f'Leg {index + 1}'
        leg.data.materials.append(material_wood)

# Build the table by calling the functions
add_table_top()
add_table_legs()


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
