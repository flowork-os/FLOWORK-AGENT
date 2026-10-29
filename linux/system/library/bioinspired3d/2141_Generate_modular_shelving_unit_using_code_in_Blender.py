# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_modular_shelving_unit_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate modular shelving unit using code in Blender

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the shelves
shelf_material = bpy.data.materials.new(name='GrayShelf')
shelf_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Function to create a shelf
def create_shelf(index, width, height, depth):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, index))
    shelf = bpy.context.object
    shelf.scale = (width, depth, height)
    shelf.name = f'Shelf_{index + 1}'
    shelf.data.materials.append(shelf_material)

# Generate shelves
shelf_dimensions = (2, 0.1, 0.5)
for idx in range(4):
    create_shelf(idx, *shelf_dimensions)

# Function to create a side support
def create_support(index, width, height, depth):
    x_position = shelf_dimensions[0] * (index * 2 - 1) / 2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_position, 0, height / 2 - 0.5))
    support = bpy.context.object
    support.scale = (width, depth, height)
    support.name = f'Support_{index + 1}'
    support.data.materials.append(shelf_material)

# Generate supports
support_dimensions = (0.1, 4, 0.5)
for idx in range(2):
    create_support(idx, *support_dimensions)


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
