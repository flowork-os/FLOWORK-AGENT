# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_desk_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of desk in python blender code

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the desk
material_desk = bpy.data.materials.new(name='Desk Material')
material_desk.diffuse_color = (0.55, 0.27, 0.07, 1)

# Create the desk top
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
desk_top = bpy.context.object

# Set dimensions of the desk top
scale_factors = [2, 1, 0.1]
desk_top.scale = scale_factors

desk_top.name = 'Desk Top'
desk_top.data.materials.append(material_desk)

# Create legs
leg_height = 0.5
leg_radius = 0.05
leg_positions = [(-1.9, -0.9, leg_height / 2), (1.9, -0.9, leg_height / 2), (-1.9, 0.9, leg_height / 2), (1.9, 0.9, leg_height / 2)]

for i in range(4):
    bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=leg_height, location=leg_positions[i])
    leg = bpy.context.object
    leg.name = f'Leg_{i + 1}'
    leg.data.materials.append(material_desk)


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
