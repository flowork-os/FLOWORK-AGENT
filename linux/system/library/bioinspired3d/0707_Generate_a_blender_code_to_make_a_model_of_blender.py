# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_blender_code_to_make_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a blender code to make a model of blender

import bpy

# Clear existing objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with varying shades
materials = [
    ("Base", (0.2, 0.2, 0.2, 1)),
    ("Control Panel", (0.1, 0.1, 0.1, 1)),
    ("Jar", (1, 1, 1, 0.1)),
    ("Lid", (0.2, 0.2, 0.2, 1))
]

for name, color in materials:
    mat = bpy.data.materials.new(name=f"{name} Material")
    mat.diffuse_color = color

# Utility function to create a primitive

def create_primitive(type, params, name):
    if type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=params[0], depth=params[1], location=params[2])
    elif type == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=params[0], location=params[1])
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(bpy.data.materials[name + ' Material'])
    return obj

# Create the Base
create_primitive('cylinder', (1, 0.5, (0, 0, 0.25)), "Base")

# Create the Control Panel
create_primitive('cube', (0.5, (0, 0.75, 0.25)), "Control Panel")
bpy.context.object.scale[2] = 0.1  # Thinner control panel

# Create the Jar
create_primitive('cylinder', (0.8, 2, (0, 0, 1.5)), "Jar")

# Create the Lid
create_primitive('cylinder', (0.85, 0.1, (0, 0, 2.55)), "Lid")


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
