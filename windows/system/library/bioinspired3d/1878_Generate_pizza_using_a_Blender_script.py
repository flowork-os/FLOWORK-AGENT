# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_pizza_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate pizza using a Blender script

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the pizza components
crust_material = bpy.data.materials.new(name='Crust Material')
crust_material.diffuse_color = (0.76, 0.60, 0.42, 1)
sauce_material = bpy.data.materials.new(name='Sauce Material')
sauce_material.diffuse_color = (0.89, 0.15, 0.07, 1)
cheese_material = bpy.data.materials.new(name='Cheese Material')
cheese_material.diffuse_color = (1.0, 0.83, 0.0, 1)
pepperoni_material = bpy.data.materials.new(name='Pepperoni Material')
pepperoni_material.diffuse_color = (0.6, 0.1, 0.1, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the pizza components
pizza_base = create_cylinder(1, 0.1, (0, 0, 0), 'Pizza Base', crust_material)
sauce_layer = create_cylinder(0.95, 0.02, (0, 0, 0.06), 'Tomato Sauce', sauce_material)
cheese_layer = create_cylinder(0.9, 0.02, (0, 0, 0.08), 'Cheese', cheese_material)

# Define positions for pepperoni slices
pepperoni_locations = [(0.5, 0.5), (-0.5, 0.5), (0.5, -0.5), (-0.5, -0.5), (0.5, 0), (-0.5, 0), (0, 0.5), (0, -0.5)]
for index, (pos_x, pos_y) in enumerate(pepperoni_locations):
    create_cylinder(0.1, 0.02, (pos_x, pos_y, 0.1), f'Pepperoni Slice {index + 1}', pepperoni_material)


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
