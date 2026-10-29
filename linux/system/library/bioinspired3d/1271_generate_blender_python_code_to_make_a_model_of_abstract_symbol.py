# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_python_code_to_make_a_model_of_abstract_symbol" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender python code to make a model of abstract symbol.

import bpy
import math

# Step 1: Clear the Scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the tori
material_gray = bpy.data.materials.new(name="Gray Material")
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to create a torus at a specified rotation

def create_torus(rotation, name):
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(0, 0, 0), rotation=rotation)
    torus = bpy.context.object
    torus.name = name
    torus.data.materials.append(material_gray)

# Step 2: Generate Tori with different rotations
create_torus((0, 0, 0), "Torus_A")
create_torus((math.pi/2, 0, 0), "Torus_B")
create_torus((0, math.pi/2, 0), "Torus_C")


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
