# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_python_blender_code_to_create_a_model_of_laundry_basket" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate python blender code to create a model of laundry basket.

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create and set up the material for the basket
basket_material = bpy.data.materials.new(name="Basket Material")
basket_material.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light gray shade

# Create the main body of the basket
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
basket_main = bpy.context.object
basket_main.name = "Basket Main"
basket_main.scale = (1, 0.7, 0.5)
basket_main.data.materials.append(basket_material)

# Define handle positions and create them
handle_coords = [(-1.2, 0, 1.2), (1.2, 0, 1.2)]
for coord in handle_coords:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=coord, rotation=(0, 1.57, 0))
    basket_handle = bpy.context.object
    basket_handle.name = "Basket Handle"
    basket_handle.data.materials.append(basket_material)


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
