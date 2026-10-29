# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_Blender_code_make_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With Blender code make drum.

import bpy

# Clear all existing objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the drum components
material_drum_body = bpy.data.materials.new(name="Body Material")
material_drum_body.diffuse_color = (0.85, 0.15, 0.15, 1)
material_drum_head = bpy.data.materials.new(name="Head Material")
material_drum_head.diffuse_color = (1.0, 1.0, 1.0, 1)
material_drum_stick = bpy.data.materials.new(name="Stick Material")
material_drum_stick.diffuse_color = (0.55, 0.25, 0.0, 1)

# Function to create drum components

def create_component(type, radius, depth, location, name, material):
    if type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    elif type == 'torus':
        bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Create the drum body
create_component('cylinder', 1, 1.5, (0, 0, 0.75), "Drum Body", material_drum_body)

# Create the drumhead
create_component('cylinder', 1, 0.05, (0, 0, 1.525), "Drumhead", material_drum_head)

# Create drumsticks
for idx in range(2):
    x_position = 1.5 * (idx * 2 - 1)
    create_component('cylinder', 0.05, 1, (x_position, 0, 0.5), f"Drumstick {idx + 1}", material_drum_stick)

# Adding decorative elements to the drum
create_component('torus', 1.1, 0.05, (0, 0, 0.3), "Pattern Top", material_drum_head)
create_component('torus', 1.1, 0.05, (0, 0, 1.2), "Pattern Bottom", material_drum_head)


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
