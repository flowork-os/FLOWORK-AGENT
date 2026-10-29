# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_Blender_code__generate_a_model_of_bookshelf" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a Blender code, generate a model of bookshelf.

import bpy

# Step 1: Clear Existing Objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define material for shelves
wood_material = bpy.data.materials.new(name="Wood Material")
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Color resembling wood

# Step 2: Generate Shelves
width = 2
height = 0.1
depth = 0.4
spacing = 0.5
shelves_count = 5

for index in range(shelves_count):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, index * spacing))
    current_shelf = bpy.context.object
    current_shelf.scale = (width / 2, depth / 2, height / 2)
    current_shelf.name = f"Shelf {index + 1}"
    current_shelf.data.materials.append(wood_material)

# Step 3: Create Side Panels
thickness = 0.05
full_height = shelves_count * spacing

for side in range(2):
    position_x = (width / 2) * (side * 2 - 1)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(position_x, 0, full_height / 2))
    current_panel = bpy.context.object
    current_panel.scale = (thickness / 2, depth / 2, full_height / 2)
    current_panel.name = f"Side Panel {side + 1}"
    current_panel.data.materials.append(wood_material)


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
