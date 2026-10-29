# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_to_generate_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code to generate a model of sandwich.

import bpy

# Clear the current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create materials with specified colors
def create_material(name, color):
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = color
    return material

# Create materials for the sandwich components
bread_mat = create_material('Bread', (0.9, 0.7, 0.5, 1))
lettuce_mat = create_material('Lettuce', (0.2, 0.8, 0.2, 1))
tomato_mat = create_material('Tomato', (0.8, 0.1, 0.1, 1))
cheese_mat = create_material('Cheese', (1, 0.9, 0.1, 1))

# Create sandwich layers using a functional approach
def add_sandwich_layer(name, position, height, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=position)
    layer = bpy.context.object
    layer.name = name
    layer.scale[2] = height
    layer.data.materials.append(material)

# Adding the layers to the sandwich
add_sandwich_layer('Bottom Bread', (0, 0, 0), 0.1, bread_mat)
add_sandwich_layer('Lettuce', (0, 0, 0.2), 0.05, lettuce_mat)
add_sandwich_layer('Tomato', (0, 0, 0.3), 0.05, tomato_mat)
add_sandwich_layer('Cheese', (0, 0, 0.4), 0.05, cheese_mat)
add_sandwich_layer('Top Bread', (0, 0, 0.6), 0.1, bread_mat)


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
