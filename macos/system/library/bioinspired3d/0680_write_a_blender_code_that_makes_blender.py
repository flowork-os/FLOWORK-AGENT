# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_blender_code_that_makes_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a blender code that makes blender

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials with distinct colors
material_base = bpy.data.materials.new(name="Main Base")
material_base.diffuse_color = (0.2, 0.2, 0.2, 1)
material_button = bpy.data.materials.new(name="Control Button")
material_button.diffuse_color = (0.8, 0.1, 0.1, 1)
material_jar = bpy.data.materials.new(name="Container Jar")
material_jar.diffuse_color = (0.8, 0.8, 0.8, 0.3)
material_lid = bpy.data.materials.new(name="Top Lid")
material_lid.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to add a cylinder with specified parameters

def add_cylinder(rad, height, pos, obj_name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=rad, depth=height, location=pos)
    new_obj = bpy.context.object
    new_obj.name = obj_name
    new_obj.data.materials.append(mat)

# Create the base of the model
add_cylinder(1, 0.5, (0, 0, 0.25), "Base", material_base)

# Add buttons to the model
for idx in range(3):
    add_cylinder(0.1, 0.2, (0.4 * (idx - 1), 0.9, 0.1), f"Button_{idx + 1}", material_button)

# Create the jar object
add_cylinder(0.8, 1.5, (0, 0, 1.25), "Jar", material_jar)

# Create the lid for the jar
add_cylinder(0.85, 0.1, (0, 0, 2), "Lid", material_lid)


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
