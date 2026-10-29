# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_building_birthday_cake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for building birthday cake.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the cake
cake_material = bpy.data.materials.new(name='Cake Material')
cake_material.diffuse_color = (0.9, 0.7, 0.5, 1)

# Function to add a cake layer

def add_cake_layer(radius, depth, z_location, layer_name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=(0, 0, z_location))
    layer = bpy.context.object
    layer.name = layer_name
    layer.data.materials.append(cake_material)
    return layer

# Create cake layers
add_cake_layer(1.5, 0.5, 0.25, 'Bottom Layer')
add_cake_layer(1.2, 0.5, 0.75, 'Middle Layer')
add_cake_layer(0.9, 0.5, 1.25, 'Top Layer')


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
