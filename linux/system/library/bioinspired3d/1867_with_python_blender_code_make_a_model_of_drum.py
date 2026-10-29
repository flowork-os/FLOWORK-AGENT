# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_python_blender_code_make_a_model_of_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with python blender code make a model of drum.

import bpy

# Clear the current mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the drum parts
mat_body = bpy.data.materials.new(name='Body Material')
mat_body.diffuse_color = (0.9, 0.1, 0.1, 1)  # Brighter red
mat_head = bpy.data.materials.new(name='Head Material')
mat_head.diffuse_color = (0.8, 0.8, 0.8, 1)  # Gray
mat_stick = bpy.data.materials.new(name='Stick Material')
mat_stick.diffuse_color = (0.4, 0.2, 0.1, 1)  # Darker brown

# Creating the drum body
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1.5, location=(0, 0, 0.75))
body = bpy.context.object
body.name = 'Drum Body'
body.data.materials.append(mat_body)

# Creating the drumhead
bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.1, location=(0, 0, 1.55))
head = bpy.context.object
head.name = 'Drumhead'
head.data.materials.append(mat_head)

# Creating the drumsticks
stick_positions = [-1.1, 1.1]
for idx, pos in enumerate(stick_positions):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.5, location=(pos, 0, 0.75), rotation=(1.57, 0, 0))
    stick = bpy.context.object
    stick.name = f'Drumstick {idx + 1}'
    stick.data.materials.append(mat_stick)


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
