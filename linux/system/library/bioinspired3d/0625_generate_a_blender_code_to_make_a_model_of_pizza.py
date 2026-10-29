# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_blender_code_to_make_a_model_of_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a blender code to make a model of pizza.

import bpy

# Start by clearing the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the pizza
crust_mat = bpy.data.materials.new(name='CrustMaterial')
crust_mat.diffuse_color = (0.8, 0.5, 0.2, 1)
cheese_mat = bpy.data.materials.new(name='CheeseMaterial')
cheese_mat.diffuse_color = (1, 0.9, 0.5, 1)

# Create crust and cheese using a function
class Pizza:
    @staticmethod
    def create_layer(radius, depth, location, name, material):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        layer = bpy.context.object
        layer.name = name
        layer.data.materials.append(material)

# Instantiate the pizza layers
Pizza.create_layer(1.1, 0.1, (0, 0, 0), 'PizzaCrust', crust_mat)
Pizza.create_layer(1, 0.02, (0, 0, 0.06), 'PizzaCheese', cheese_mat)


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
