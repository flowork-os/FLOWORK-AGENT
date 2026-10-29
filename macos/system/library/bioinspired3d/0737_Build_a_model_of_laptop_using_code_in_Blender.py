# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_a_model_of_laptop_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build a model of laptop using code in Blender

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the model
material_gray = bpy.data.materials.new(name="Gray Material")
material_gray.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to create a cube with specific properties

def create_cube(size, location, scale, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.name = name
    cube.data.materials.append(material_gray)
    return cube

# Create the base of the model
base_cube = create_cube(2, (0, 0, 0.1), (1, 1, 0.05), "Base")

# Create the keyboard component
keyboard_cube = create_cube(1.8, (0, 0, 0.15), (1, 1, 0.01), "Keyboard")

# Create the screen
screen_cube = create_cube(2, (0, 0.95, 1.05), (1, 1, 0.05), "Screen")
screen_cube.rotation_euler[0] = 1.5708  # Rotate to vertical

# Create multiple ports using a loop
for index in range(3):
    port_location = (-1, 0.9 - index * 0.3, 0.1)
    create_cube(0.1, port_location, (1, 1, 0.02), f"Port {index + 1}")


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
