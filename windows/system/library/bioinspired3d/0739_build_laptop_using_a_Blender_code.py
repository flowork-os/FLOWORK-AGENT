# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_laptop_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build laptop using a Blender code

import bpy

# Clear the current meshes in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material
material = bpy.data.materials.new(name="Slate")
material.diffuse_color = (0.25, 0.25, 0.25, 1)  # Slate color

# Create a function to add a cube with specified parameters

def add_cube(size, position, scale_factors, object_name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    obj = bpy.context.object
    obj.scale = scale_factors
    obj.name = object_name
    obj.data.materials.append(material)

# Add the base
add_cube(2, (0, 0, 0.1), (1, 1, 0.05), "Base")

# Add the keyboard
add_cube(1.8, (0, 0, 0.15), (1, 1, 0.01), "Keyboard")

# Add the screen
add_cube(2, (0, 0.95, 1.05), (1, 1, 0.05), "Screen")
bpy.context.object.rotation_euler[0] = 1.5708  # Rotate to vertical

# Create ports in a loop
for index in range(3):
    add_cube(0.1, (-1, 0.9 - index * 0.3, 0.1), (1, 1, 0.02), f"Port {index + 1}")


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
