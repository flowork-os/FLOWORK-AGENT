# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_transformer_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of transformer in a blender code

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
material_body = bpy.data.materials.new(name="Material Body")
material_body.diffuse_color = (0.6, 0.6, 0.6, 1)  # Light gray for the main body
material_coil = bpy.data.materials.new(name="Material Coil")
material_coil.diffuse_color = (0.2, 0.2, 0.2, 1)  # Darker gray for coils

# Function to create the main body

def create_body():
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))
    body_object = bpy.context.object
    body_object.name = "Main Body"
    body_object.data.materials.append(material_body)

# Function to create coils

def create_coils():
    for index in range(3):
        position_z = -0.5 + index * 0.6
        bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.1, location=(0, 0, position_z))
        coil_object = bpy.context.object
        coil_object.name = f"Coil_{index + 1}"
        coil_object.data.materials.append(material_coil)

# Execute functions to create the model
create_body()
create_coils()


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
