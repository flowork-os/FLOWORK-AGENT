# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_code_that_makes_a_model_of_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender code that makes a model of pizza.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials for the pizza components
material_crust = bpy.data.materials.new(name='PizzaCrust')
material_crust.diffuse_color = (0.8, 0.6, 0.4, 1)
material_sauce = bpy.data.materials.new(name='PizzaSauce')
material_sauce.diffuse_color = (0.8, 0.1, 0.1, 1)
material_cheese = bpy.data.materials.new(name='PizzaCheese')
material_cheese.diffuse_color = (1.0, 0.9, 0.5, 1)

# Create the crust, sauce, and cheese layers using a single function

def add_pizza_layer(radius, height, position, layer_name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    layer = bpy.context.object
    layer.name = layer_name
    layer.data.materials.append(mat)

# Construct the pizza layers
add_pizza_layer(1.1, 0.1, (0, 0, 0), 'CrustLayer', material_crust)
add_pizza_layer(1.0, 0.02, (0, 0, 0.06), 'SauceLayer', material_sauce)
add_pizza_layer(0.95, 0.02, (0, 0, 0.08), 'CheeseLayer', material_cheese)


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
