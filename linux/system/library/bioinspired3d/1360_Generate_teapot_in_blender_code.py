# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_teapot_in_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate teapot in blender code

import bpy
import math

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a brown material for the teapot
teapot_brown_material = bpy.data.materials.new(name='Brown Teapot')
teapot_brown_material.diffuse_color = (0.8, 0.5, 0.3, 1)  # Earthy brown tone

# Function to add a new mesh object

def add_mesh(primitive_type, **params):
    if primitive_type == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(**params)
    elif primitive_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(**params)
    else:
        bpy.ops.mesh.primitive_torus_add(**params)
    return bpy.context.object

# Construct the teapot
body_object = add_mesh('sphere', radius=1, location=(0, 0, 0))
body_object.name = 'Teapot Body'
body_object.data.materials.append(teapot_brown_material)

spout_object = add_mesh('cylinder', radius=0.1, depth=1, location=(1, 0, 0))
spout_object.name = 'Teapot Spout'
spout_object.rotation_euler = (0, math.pi / 6, 0)
spout_object.location = (0.8, 0, 0.4)
spout_object.data.materials.append(teapot_brown_material)

handle_object = add_mesh('torus', major_radius=0.6, minor_radius=0.1, location=(-1, 0, 0))
handle_object.name = 'Teapot Handle'
handle_object.rotation_euler = (math.pi / 2, 0, 0)
handle_object.location = (-0.8, 0, 0.4)
handle_object.data.materials.append(teapot_brown_material)

lid_object = add_mesh('sphere', radius=0.5, location=(0, 0, 1))
lid_object.name = 'Teapot Lid'
lid_object.scale[2] = 0.5
lid_object.data.materials.append(teapot_brown_material)

knob_object = add_mesh('sphere', radius=0.1, location=(0, 0, 1.3))
knob_object.name = 'Teapot Knob'
knob_object.data.materials.append(teapot_brown_material)


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
