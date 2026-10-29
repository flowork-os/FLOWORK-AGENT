# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_code_in_Blender_make_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using code in Blender make sandwich

import bpy

# Start by clearing all current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for each component of the sandwich
bread_material = bpy.data.materials.new(name='Bread Material')
bread_material.diffuse_color = (0.96, 0.87, 0.70, 1)
lettuce_material = bpy.data.materials.new(name='Lettuce Material')
lettuce_material.diffuse_color = (0.13, 0.55, 0.13, 1)
tomato_material = bpy.data.materials.new(name='Tomato Material')
tomato_material.diffuse_color = (0.89, 0.15, 0.07, 1)
cheese_material = bpy.data.materials.new(name='Cheese Material')
cheese_material.diffuse_color = (1.0, 0.83, 0.0, 1)

# Helper function to add a cube with a specific material and scale
def add_sandwich_layer(layer_name, position, height, mat):
    bpy.ops.mesh.primitive_cube_add(size=2, location=position)
    layer = bpy.context.object
    layer.name = layer_name
    layer.scale[2] = height
    layer.data.materials.append(mat)

# Create each layer of the sandwich
add_sandwich_layer('Bottom Bread', (0, 0, 0), 0.1, bread_material)
add_sandwich_layer('Lettuce', (0, 0, 0.2), 0.05, lettuce_material)
add_sandwich_layer('Tomato', (0, 0, 0.3), 0.05, tomato_material)
add_sandwich_layer('Cheese', (0, 0, 0.4), 0.05, cheese_material)
add_sandwich_layer('Top Bread', (0, 0, 0.6), 0.1, bread_material)


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
