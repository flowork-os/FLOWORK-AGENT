# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_creates_a_model_of_armchair" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that creates a model of armchair.

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials
wood_texture = bpy.data.materials.new(name='WoodTexture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)
cushion_texture = bpy.data.materials.new(name='CushionTexture')
cushion_texture.diffuse_color = (0.8, 0.4, 0.4, 1)

# Create furniture components
legs = []
for k in range(4):
    leg_position = (0.6 * (k % 2) - 0.3, 0.6 * (k // 2) - 0.3, -0.5)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.0, location=leg_position)
    leg = bpy.context.object
    leg.name = f'Leg_{k + 1}'
    leg.data.materials.append(wood_texture)
    legs.append(leg)

# Create the seat
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0, 0, 0.1))
seat_component = bpy.context.object
seat_component.name = 'Seat'
seat_component.scale = (1, 1, 0.2)
seat_component.data.materials.append(cushion_texture)

# Backrest creation
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0, -0.55, 0.75))
backrest_component = bpy.context.object
backrest_component.name = 'Backrest'
backrest_component.scale = (1, 0.1, 1.5)
backrest_component.data.materials.append(wood_texture)

# Create armrests
for l in range(2):
    arm_position = (0.55 * (l * 2 - 1), 0, 0.5)
    bpy.ops.mesh.primitive_cube_add(size=1.2, location=arm_position)
    armrest_component = bpy.context.object
    armrest_component.name = f'Armrest_{l + 1}'
    armrest_component.scale = (0.1, 1, 0.2)
    armrest_component.data.materials.append(wood_texture)


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
