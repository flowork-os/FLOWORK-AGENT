# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_script_to_build_a_model_of_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender script to build a model of coffee table.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the table
wooden_material = bpy.data.materials.new(name='WoodenFinish')
wooden_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Color representing wood

# Object-oriented approach to create a table
class Table:
    def __init__(self):
        self.create_tabletop()
        self.create_legs()

    def create_tabletop(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
        self.top = bpy.context.object
        self.top.scale = (2, 1, 0.1)
        self.top.name = 'Tabletop'
        self.top.data.materials.append(wooden_material)

    def create_legs(self):
        leg_height = 0.5
        leg_radius = 0.05
        positions = [(-1.9, -0.9, leg_height / 2), (1.9, -0.9, leg_height / 2), (-1.9, 0.9, leg_height / 2), (1.9, 0.9, leg_height / 2)]
        for pos in positions:
            bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=leg_height, location=pos)
            leg = bpy.context.object
            leg.name = 'TableLeg'
            leg.data.materials.append(wooden_material)

# Instantiate the Table class to create the table
Table()


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
