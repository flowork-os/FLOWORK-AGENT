# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_construct_a_model_of_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to construct a model of pizza.

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create new materials for the pizza layers
crust_material = bpy.data.materials.new(name='CrustMaterial')
crust_material.diffuse_color = (0.8, 0.6, 0.4, 1)
sauce_material = bpy.data.materials.new(name='SauceMaterial')
sauce_material.diffuse_color = (0.8, 0.1, 0.1, 1)
cheese_material = bpy.data.materials.new(name='CheeseMaterial')
cheese_material.diffuse_color = (1.0, 0.9, 0.5, 1)

# Function to create a cylinder layer

def create_layer(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    layer = bpy.context.object
    layer.name = name
    layer.data.materials.append(material)

# Create the pizza layers
create_layer(1.1, 0.1, (0, 0, 0), 'Crust', crust_material)
create_layer(1.0, 0.02, (0, 0, 0.06), 'Sauce', sauce_material)
create_layer(0.95, 0.02, (0, 0, 0.08), 'Cheese', cheese_material)


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
