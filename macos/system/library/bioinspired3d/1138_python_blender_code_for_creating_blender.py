# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_creating_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for creating blender.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials with different names
material_blender = bpy.data.materials.new(name='Material Blender')
material_blender.diffuse_color = (0.5, 0.5, 0.5, 1)
material_switch = bpy.data.materials.new(name='Material Switch')
material_switch.diffuse_color = (0.2, 0.2, 0.2, 1)

# Create the base, jar, and lid using a loop
objects_info = [
    (1, 0.5, (0, 0, 0.25), 'Blender Base'),
    (0.8, 1.5, (0, 0, 1.25), 'Blender Jar'),
    (0.85, 0.1, (0, 0, 2), 'Blender Lid')
]

for radius, depth, loc, name in objects_info:
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material_blender)

# Create the switch
bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0.9, 0, 0.25))
switch = bpy.context.object
switch.name = 'On/Off Switch'
switch.data.materials.append(material_switch)


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
