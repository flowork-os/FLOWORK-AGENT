# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_code_that_makes_a_model_of_desk" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender code that makes a model of desk.

import bpy

# Start fresh by clearing the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize a wood-like material
desk_material = bpy.data.materials.new(name='WoodFinish')
desk_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to build a desk
class Desk:
    def __init__(self):
        self.create_top()
        self.create_legs()

    def create_top(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
        top = bpy.context.object
        top.scale = (2, 1, 0.1)
        top.name = 'Desk Surface'
        top.data.materials.append(desk_material)

    def create_legs(self):
        leg_height = 0.5
        leg_radius = 0.05
        leg_positions = [(-1.9, -0.9, leg_height / 2), (1.9, -0.9, leg_height / 2), (-1.9, 0.9, leg_height / 2), (1.9, 0.9, leg_height / 2)]

        for index, position in enumerate(leg_positions):
            bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=leg_height, location=position)
            leg = bpy.context.object
            leg.name = f'Leg_{index + 1}'
            leg.data.materials.append(desk_material)

# Create the desk
Desk()


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
