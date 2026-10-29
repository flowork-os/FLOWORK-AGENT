# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_blender_code_that_makes_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a blender code that makes blender

import bpy

# Remove all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials
base_mat = bpy.data.materials.new(name="Main Base")
base_mat.diffuse_color = (0.1, 0.1, 0.1, 1)

red_mat = bpy.data.materials.new(name="Red Button")
red_mat.diffuse_color = (0.9, 0.1, 0.1, 1)

trans_mat = bpy.data.materials.new(name="Transparent Jar")
trans_mat.diffuse_color = (1, 1, 1, 0.15)

# Create base as a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
base_object = bpy.context.object
base_object.name = "Base Object"
base_object.data.materials.append(base_mat)

# Create the jar
bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=2, location=(0, 0, 1.5))
jar_object = bpy.context.object
jar_object.name = "Jar Object"
jar_object.data.materials.append(trans_mat)

# Create buttons using a loop
for button_index in range(3):
    button_x = -0.5 + button_index * 0.5
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(button_x, 0.9, 0.15))
    button_object = bpy.context.object
    button_object.name = f"Button_{button_index + 1}"
    button_object.data.materials.append(red_mat)


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
