# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_creates_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that creates a model of sandwich.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for sandwich components
materials = {
    'Bread': (0.9, 0.7, 0.5, 1),
    'Lettuce': (0.2, 0.8, 0.2, 1),
    'Tomato': (0.8, 0.1, 0.1, 1),
    'Cheese': (1, 0.9, 0.3, 1),
    'Meat': (0.6, 0.3, 0.2, 1)
}

# Function to create a material
def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

# Create materials from the defined colors
bread_mat = create_material('Bread Color', materials['Bread'])
lettuce_mat = create_material('Lettuce Color', materials['Lettuce'])
tomato_mat = create_material('Tomato Color', materials['Tomato'])
cheese_mat = create_material('Cheese Color', materials['Cheese'])
meat_mat = create_material('Meat Color', materials['Meat'])

# Function to add a cube with a specific material
def add_cube(name, loc, scale, mat):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)

# Add sandwich layers
add_cube('Bottom Bread', (0, 0, 0), (1, 1, 0.1), bread_mat)
add_cube('Lettuce', (0, 0, 0.2), (1, 1, 0.05), lettuce_mat)
add_cube('Tomato', (0, 0, 0.3), (1, 1, 0.05), tomato_mat)
add_cube('Cheese', (0, 0, 0.4), (1, 1, 0.05), cheese_mat)
add_cube('Meat', (0, 0, 0.5), (1, 1, 0.1), meat_mat)
add_cube('Top Bread', (0, 0, 0.7), (1, 1, 0.1), bread_mat)


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
