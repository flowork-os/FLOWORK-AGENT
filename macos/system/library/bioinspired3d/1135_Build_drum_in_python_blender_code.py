# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_drum_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build drum in python blender code

import bpy
import math

# Remove all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions for the drum parts
material_drum_body = bpy.data.materials.new(name='Drum Body')
material_drum_body.diffuse_color = (0.5, 0.2, 0.1, 1)
material_drum_head = bpy.data.materials.new(name='Drumhead')
material_drum_head.diffuse_color = (0.9, 0.9, 0.9, 1)
material_tension_rod = bpy.data.materials.new(name='Tension Rod')
material_tension_rod.diffuse_color = (0.8, 0.8, 0.8, 1)
material_drumstick = bpy.data.materials.new(name='Drumstick')
material_drumstick.diffuse_color = (0.7, 0.4, 0.1, 1)

# Create the drum structure

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1.5, location=(0, 0, 0.75))
drum_body = bpy.context.object

drum_body.name = 'Drum Body'
drum_body.data.materials.append(material_drum_body)

bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.05, location=(0, 0, 1.525))
drum_head = bpy.context.object

drum_head.name = 'Drumhead'
drum_head.data.materials.append(material_drum_head)

# Adding tension rods
for i in range(8):
    theta = 2 * math.pi * i / 8
    x_pos = 1.1 * math.cos(theta)
    y_pos = 1.1 * math.sin(theta)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=1.6, location=(x_pos, y_pos, 0.8))
    tension_rod = bpy.context.object
    tension_rod.name = f'Tension Rod {i + 1}'
    tension_rod.data.materials.append(material_tension_rod)

# Create drumsticks
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(1.5, 0, 0.5), rotation=(0, math.pi / 4, 0))
drumstick_a = bpy.context.object

drumstick_a.name = 'Drumstick 1'
drumstick_a.data.materials.append(material_drumstick)

bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(1.5, 0.2, 0.5), rotation=(0, math.pi / 4, 0))
drumstick_b = bpy.context.object

drumstick_b.name = 'Drumstick 2'
drumstick_b.data.materials.append(material_drumstick)


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
