# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_blender_code_create_a_model_of_laundry_basket" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a blender code create a model of laundry basket.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material for the basket and apply a light gray color
basket_material = bpy.data.materials.new(name="Basket Material")
basket_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Add the basket body using a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
main_basket = bpy.context.object
main_basket.name = "Basket Body"
main_basket.scale = (1, 0.7, 0.5)
main_basket.data.materials.append(basket_material)

# Create the basket handles by looping through positions
handle_locations = [(-1.2, 0, 1.2), (1.2, 0, 1.2)]
for location in handle_locations:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=location, rotation=(0, 1.57, 0))
    handle_item = bpy.context.object
    handle_item.name = "Handle"
    handle_item.data.materials.append(basket_material)


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
