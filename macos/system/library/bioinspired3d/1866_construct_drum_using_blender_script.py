# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_drum_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct drum using blender script

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the drum components
material_drum_body = bpy.data.materials.new(name='Drum Body')
material_drum_body.diffuse_color = (0.7, 0.2, 0.2, 1)  # Slightly different red
material_drum_head = bpy.data.materials.new(name='Drum Head')
material_drum_head.diffuse_color = (0.85, 0.85, 0.85, 1)  # Soft gray
material_drum_stick = bpy.data.materials.new(name='Drum Stick')
material_drum_stick.diffuse_color = (0.55, 0.25, 0.1, 1)  # Lighter brown

# Create the drum body
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1.5, location=(0, 0, 0.75))
drum_body = bpy.context.object
bpy.context.object.name = 'Drum Body'
drum_body.data.materials.append(material_drum_body)

# Create the drumhead
bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.1, location=(0, 0, 1.55))
drum_head = bpy.context.object
bpy.context.object.name = 'Drumhead'
drum_head.data.materials.append(material_drum_head)

# Create drumsticks using a loop
for i in range(2):
    x_position = 1.1 * (i * 2 - 1)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.5, location=(x_position, 0, 0.75), rotation=(1.57, 0, 0))
    stick = bpy.context.object
    stick.name = f'Drumstick {i + 1}'
    stick.data.materials.append(material_drum_stick)


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
