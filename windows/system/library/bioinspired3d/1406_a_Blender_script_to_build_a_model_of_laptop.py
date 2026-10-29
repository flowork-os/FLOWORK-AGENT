# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_build_a_model_of_laptop" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to build a model of laptop.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the laptop
black_material = bpy.data.materials.new(name="BlackMaterial")
black_material.diffuse_color = (0.0, 0.0, 0.0, 1)  # Setting color to black

# Function to create a cube with specific parameters

def create_cube(size, location, scale, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.name = name
    cube.data.materials.append(material)
    return cube

# Build the laptop base
create_cube(2, (0, 0, 0.1), (1.5, 1, 0.05), "LaptopBase", black_material)

# Build the screen
create_cube(2, (0, 1.05, 1.1), (1.5, 0.05, 1), "LaptopScreen", black_material)

# Function to create keyboard keys

def create_keyboard(rows, cols, key_size, key_spacing):
    for row in range(rows):
        for col in range(cols):
            x = (col - cols / 2) * (key_size + key_spacing) + (key_size + key_spacing) / 2
            y = (row - rows / 2) * (key_size + key_spacing) + (key_size + key_spacing) / 2
            create_cube(key_size, (x, y, 0.15), (1, 1, 1), f"Key_{row}_{col}", black_material)

# Create the keyboard
create_keyboard(5, 10, 0.2, 0.05)


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
