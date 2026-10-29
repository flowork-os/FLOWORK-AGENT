# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_script_to_create_a_model_of_modular_shelving_unit" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender script to create a model of modular shelving unit

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the shelves
shelf_material = bpy.data.materials.new(name='ShelfMaterial')
shelf_material.diffuse_color = (0.75, 0.75, 0.75, 1)  # Soft gray color

# Function to create a shelf
def create_shelf(index):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, index * 1.2))
    shelf = bpy.context.object
    shelf.scale = (2, 0.5, 0.1)
    shelf.name = f'Shelf_{index + 1}'
    shelf.data.materials.append(shelf_material)

# Generate shelves
for i in range(3):
    create_shelf(i)

# Function to create vertical supports
def create_support(index):
    x = (index % 2) * (2 - 0.1) - (2 / 2 - 0.1 / 2)
    y = (index // 2) * (0.5 - 0.1) - (0.5 / 2 - 0.1 / 2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 3.5 / 2 - 0.1 / 2))
    support = bpy.context.object
    support.scale = (0.1, 0.1, 3.5)
    support.name = f'Support_{index + 1}'
    support.data.materials.append(shelf_material)

# Generate supports
for i in range(4):
    create_support(i)


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
