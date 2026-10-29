# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_constructing_a_model_of_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for constructing a model of drum.

import bpy
import math

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the drum components
mat_body = bpy.data.materials.new(name='Drum Body')
mat_body.diffuse_color = (0.8, 0.2, 0.2, 1)
mat_head = bpy.data.materials.new(name='Drumhead')
mat_head.diffuse_color = (0.9, 0.9, 0.9, 1)
mat_rods = bpy.data.materials.new(name='Tension Rods')
mat_rods.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to create a drum part
def add_drumpart(radius, depth, position, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    part = bpy.context.object
    part.name = name
    part.data.materials.append(material)

# Create drum body
add_drumpart(1, 1.5, (0, 0, 0.75), 'Drum Body', mat_body)

# Create drumhead
add_drumpart(1.05, 0.1, (0, 0, 1.55), 'Drumhead', mat_head)

# Generate tension rods
for i in range(8):
    angle = i * (math.pi * 2 / 8)
    rod_x = 1.05 * math.cos(angle)
    rod_y = 1.05 * math.sin(angle)
    add_drumpart(0.05, 1.6, (rod_x, rod_y, 0.8), f'Tension Rod {i + 1}', mat_rods)


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
