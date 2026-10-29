# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_python_blender_code_to_make_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write python blender code to make transformer.

import bpy

# Clean the scene by deleting all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the body and coils
body_mat = bpy.data.materials.new(name="Main Material")
body_mat.diffuse_color = (0.5, 0.5, 0.5, 1)
coil_mat = bpy.data.materials.new(name="Secondary Material")
coil_mat.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to create the body

def add_body():
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))
    body_model = bpy.context.object
    body_model.name = "Body Shape"
    body_model.data.materials.append(body_mat)

# Function to add coils

def add_coils():
    for index in range(3):
        z_coord = -0.6 + index * 0.6
        bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.1, location=(0, 0, z_coord))
        coil_model = bpy.context.object
        coil_model.name = f"Coil Part {index + 1}"
        coil_model.data.materials.append(coil_mat)

# Create the body and coils
add_body()
add_coils()


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
