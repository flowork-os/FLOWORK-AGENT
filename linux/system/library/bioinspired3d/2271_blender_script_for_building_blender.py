# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_for_building_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script for building blender.

import bpy

# Clear all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with descriptive names
material_base = bpy.data.materials.new(name='Material Base')
material_base.diffuse_color = (0.1, 0.1, 0.1, 1)
material_jug = bpy.data.materials.new(name='Material Jug')
material_jug.diffuse_color = (0.8, 0.8, 0.8, 0.5)
material_button = bpy.data.materials.new(name='Material Button')
material_button.diffuse_color = (0.2, 0.2, 0.2, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Build the components
base_obj = create_cylinder(1, 0.5, (0, 0, 0.25), 'Base', material_base)
jug_obj = create_cylinder(0.8, 2, (0, 0, 1.5), 'Jug', material_jug)
lid_obj = create_cylinder(0.85, 0.1, (0, 0, 2.55), 'Lid', material_base)

# Create buttons using a loop
for index in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0.5 - index * 0.3, 0.9, 0.25))
    button_obj = bpy.context.object
    button_obj.name = f'Button_{index + 1}'
    button_obj.data.materials.append(material_button)


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
