# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_laptop_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of laptop in blender python code

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a black material
material_black = bpy.data.materials.new(name="MaterialBlack")
material_black.diffuse_color = (0, 0, 0, 1)  # Black color

# Create the base shape for the laptop
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.1))
base_shape = bpy.context.object
base_shape.scale = (1.5, 1, 0.05)
base_shape.name = "LaptopBase"
base_shape.data.materials.append(material_black)

# Create the screen part
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 1.05, 1.1))
screen_shape = bpy.context.object
screen_shape.scale = (1.5, 0.05, 1)
screen_shape.name = "LaptopScreen"
screen_shape.data.materials.append(material_black)

# Function to generate keys for the keyboard
def generate_keyboard(rows, cols, key_dim, spacing):
    for r in range(rows):
        for c in range(cols):
            x_pos = (c - cols / 2) * (key_dim + spacing) + (key_dim + spacing) / 2
            y_pos = (r - rows / 2) * (key_dim + spacing) + (key_dim + spacing) / 2
            bpy.ops.mesh.primitive_cube_add(size=key_dim, location=(x_pos, y_pos, 0.15))
            key = bpy.context.object
            key.name = f"Key_{r}_{c}"
            key.data.materials.append(material_black)

# Create the keyboard layout
generate_keyboard(5, 10, 0.2, 0.05)


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
