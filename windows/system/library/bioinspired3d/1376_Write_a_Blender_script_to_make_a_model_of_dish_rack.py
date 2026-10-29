# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_Blender_script_to_make_a_model_of_dish_rack" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a Blender script to make a model of dish rack

import bpy

# Clear the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the metallic finish
metallic_material = bpy.data.materials.new(name='Metallic Finish')
metallic_material.diffuse_color = (0.7, 0.7, 0.7, 1)  # Light gray color

# Function to create a cube with specific parameters

def create_cube(size, location, name, scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(metallic_material)
    return cube

# Create the main base
base_cube = create_cube(2, (0, 0, 0.1), 'Main Base', (1, 1, 0.025))  # Flattened base

# Create side bars
for index in range(2):
    x_position = 0.9 * (index * 2 - 1)
    create_cube(2, (x_position, 0, 0.6), f'Side Bar {index + 1}', (0.025, 1, 0.5))

# Create racks
for index in range(5):
    y_position = 0.8 * (index / 4) - 0.4
    create_cube(2, (0, y_position, 0.6), f'Rack {index + 1}', (0.9, 0.025, 0.025))


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
