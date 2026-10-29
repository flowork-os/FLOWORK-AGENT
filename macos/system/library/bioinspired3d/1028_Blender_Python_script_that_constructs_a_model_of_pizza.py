# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_constructs_a_model_of_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that constructs a model of pizza.

import bpy
import math

# Delete all existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to set up a material
def setup_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

# Define pizza materials with distinct colors
material_dough = setup_material("Dough", (0.92, 0.76, 0.56, 1))
material_sauce = setup_material("Sauce", (0.8, 0.1, 0.1, 1))
material_cheese = setup_material("Cheese", (0.95, 0.87, 0.45, 1))
material_pepperoni = setup_material("Pepperoni", (0.6, 0.1, 0.1, 1))

# Create the pizza base using a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.1, location=(0, 0, 0))
base_object = bpy.context.object
base_object.name = "Pizza Base"
base_object.data.materials.append(material_dough)

# Create sauce and cheese layers
bpy.ops.mesh.primitive_cylinder_add(radius=0.95, depth=0.02, location=(0, 0, 0.06))
sauce_object = bpy.context.object
sauce_object.name = "Sauce Layer"
sauce_object.data.materials.append(material_sauce)

bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=0.02, location=(0, 0, 0.08))
cheese_object = bpy.context.object
cheese_object.name = "Cheese Layer"
cheese_object.data.materials.append(material_cheese)

# Generate pepperoni slices in a circular pattern
for index in range(8):
    theta = index * (math.pi / 4)
    x_coord = 0.65 * math.cos(theta)
    y_coord = 0.65 * math.sin(theta)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.02, location=(x_coord, y_coord, 0.1))
    pepperoni_object = bpy.context.object
    pepperoni_object.name = f"Pepperoni {index + 1}"
    pepperoni_object.data.materials.append(material_pepperoni)


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
