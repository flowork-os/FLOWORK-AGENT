# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_that_creates_a_model_of_modular_shelving" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code that creates a model of modular shelving.

import bpy

# Clear the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material for the shelves
shelf_mat = bpy.data.materials.new(name="ShelfMaterial")
shelf_mat.diffuse_color = (0.85, 0.85, 0.85, 1)  # A gentle gray tone

# Create shelves using a function
def add_shelves(num):
    shelf_thickness = 0.1
    shelf_width = 2
    shelf_depth = 0.5
    for i in range(num):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i * (shelf_thickness + 0.5)))
        shelf = bpy.context.object
        shelf.scale = (shelf_width, shelf_depth, shelf_thickness)
        shelf.name = f"Shelf_{i + 1}"
        shelf.data.materials.append(shelf_mat)

add_shelves(3)

# Create supports using a function
def add_supports(num):
    support_radius = 0.05
    support_height = 2
    for i in range(num):
        x_coord = (i % 2) * 2 - 1  # Centering supports
        y_coord = (i // 2) * 0.5 - 0.25  # Centering supports
        bpy.ops.mesh.primitive_cylinder_add(radius=support_radius, depth=support_height, location=(x_coord, y_coord, support_height / 2))
        support = bpy.context.object
        support.name = f"Support_{i + 1}"
        support.data.materials.append(shelf_mat)

add_supports(4)


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
