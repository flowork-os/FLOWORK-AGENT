# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_script_to_create_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender script to create blender

import bpy

# Remove existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials with specific colors
base_material = bpy.data.materials.new(name='BaseMaterial')
base_material.diffuse_color = (0.1, 0.1, 0.1, 1)
jug_material = bpy.data.materials.new(name='JugMaterial')
jug_material.diffuse_color = (0.8, 0.8, 0.8, 0.5)
button_material = bpy.data.materials.new(name='ButtonMaterial')
button_material.diffuse_color = (0.2, 0.2, 0.2, 1)

# Class to represent a 3D object
class ThreeDObject:
    def __init__(self, shape_func, params, name, material):
        shape_func(**params)
        self.object = bpy.context.object
        self.object.name = name
        self.object.data.materials.append(material)

# Create the base, jug, and lid
ThreeDObject(bpy.ops.mesh.primitive_cylinder_add, {'radius': 1, 'depth': 0.5, 'location': (0, 0, 0.25)}, 'Base', base_material)
ThreeDObject(bpy.ops.mesh.primitive_cylinder_add, {'radius': 0.8, 'depth': 2, 'location': (0, 0, 1.5)}, 'Jug', jug_material)
ThreeDObject(bpy.ops.mesh.primitive_cylinder_add, {'radius': 0.85, 'depth': 0.1, 'location': (0, 0, 2.55)}, 'Lid', base_material)

# Create buttons at specified locations
button_positions = [(0.5, 0.9), (0.2, 0.9), (-0.1, 0.9)]
for idx, pos in enumerate(button_positions):
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(pos[0], pos[1], 0.25))
    button = bpy.context.object
    button.name = f'Button_{idx + 1}'
    button.data.materials.append(button_material)


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
