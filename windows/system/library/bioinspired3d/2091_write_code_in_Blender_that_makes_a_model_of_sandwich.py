# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_code_in_Blender_that_makes_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write code in Blender that makes a model of sandwich.

import bpy

# Clear all existing objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the sandwich
mat_bread = bpy.data.materials.new(name='Bread Material')
mat_bread.diffuse_color = (0.94, 0.86, 0.68, 1)
mat_lettuce = bpy.data.materials.new(name='Lettuce Material')
mat_lettuce.diffuse_color = (0.14, 0.56, 0.14, 1)
mat_tomato = bpy.data.materials.new(name='Tomato Material')
mat_tomato.diffuse_color = (0.9, 0.16, 0.09, 1)
mat_cheese = bpy.data.materials.new(name='Cheese Material')
mat_cheese.diffuse_color = (1.0, 0.84, 0.0, 1)

# Using a class to structure the sandwich creation
class Sandwich:
    def __init__(self):
        self.components = []

    def add_layer(self, name, location, scale, material):
        bpy.ops.mesh.primitive_cube_add(size=2, location=location)
        layer = bpy.context.object
        layer.name = name
        layer.scale[2] = scale
        layer.data.materials.append(material)
        self.components.append(layer)

# Create the sandwich
sandwich = Sandwich()

sandwich.add_layer('Base Bread', (0, 0, 0), 0.1, mat_bread)
sandwich.add_layer('Lettuce', (0, 0, 0.2), 0.05, mat_lettuce)
sandwich.add_layer('Tomato', (0, 0, 0.3), 0.05, mat_tomato)
sandwich.add_layer('Cheese', (0, 0, 0.4), 0.05, mat_cheese)
sandwich.add_layer('Top Bread', (0, 0, 0.6), 0.1, mat_bread)


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
