# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_constructing_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for constructing blender.

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the blender components
body_mat = bpy.data.materials.new(name='Body Material')
body_mat.diffuse_color = (0.5, 0.5, 0.5, 1)
switch_mat = bpy.data.materials.new(name='Switch Material')
switch_mat.diffuse_color = (0.2, 0.2, 0.2, 1)

# Create a function to add a mesh object
def add_mesh_object(mesh_type, params, name, material):
    if mesh_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=params[0], depth=params[1], location=params[2])
    elif mesh_type == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=params[0], location=params[1])
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the blender components
add_mesh_object('cylinder', (1, 0.5, (0, 0, 0.25)), 'Blender Base', body_mat)
add_mesh_object('cylinder', (0.8, 1.5, (0, 0, 1.25)), 'Blender Jar', body_mat)
add_mesh_object('cylinder', (0.85, 0.1, (0, 0, 2)), 'Blender Lid', body_mat)

# Create the On/Off switch
add_mesh_object('cube', (0.2, (0.9, 0, 0.25)), 'On/Off Switch', switch_mat)


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
