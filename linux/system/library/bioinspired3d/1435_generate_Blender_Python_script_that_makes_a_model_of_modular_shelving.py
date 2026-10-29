# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_Python_script_that_makes_a_model_of_modular_shelving" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender Python script that makes a model of modular shelving

import bpy

# Step 1: Clear the Scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the shelves
shelf_material = bpy.data.materials.new(name="ShelfMaterial")
shelf_material.diffuse_color = (0.7, 0.7, 0.7, 1)  # Soft gray shade

# Step 2: Create Shelves
height_of_shelf = 0.1
width_of_shelf = 2
depth_of_shelf = 0.5

for index in range(3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, index * (height_of_shelf + 0.5)))
    shelf_object = bpy.context.object
    shelf_object.scale = (width_of_shelf, depth_of_shelf, height_of_shelf)
    shelf_object.name = f"Shelf_{index + 1}"
    shelf_object.data.materials.append(shelf_material)

# Step 3: Create Vertical Supports
radius_of_support = 0.05
height_of_support = 2

for index in range(4):
    x_position = (index % 2) * width_of_shelf - width_of_shelf / 2
    y_position = (index // 2) * depth_of_shelf - depth_of_shelf / 2
    bpy.ops.mesh.primitive_cylinder_add(radius=radius_of_support, depth=height_of_support, location=(x_position, y_position, height_of_support / 2))
    support_object = bpy.context.object
    support_object.name = f"Support_{index + 1}"
    support_object.data.materials.append(shelf_material)


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
