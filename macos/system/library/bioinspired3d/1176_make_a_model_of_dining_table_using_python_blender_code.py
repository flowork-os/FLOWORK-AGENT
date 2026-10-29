# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_dining_table_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of dining table using python blender code

import bpy

# Remove all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material for the table
wood_material = bpy.data.materials.new(name='Table Wood')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)

# Create the table structure using classes
class Table:
    def __init__(self):
        self.create_table_top()
        self.create_table_legs()

    def create_table_top(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
        top_surface = bpy.context.object
        top_surface.scale[0] = 2.5  # Length
        top_surface.scale[1] = 1.2  # Width
        top_surface.scale[2] = 0.1  # Thickness
        top_surface.name = 'Table Top'
        top_surface.data.materials.append(wood_material)

    def create_table_legs(self):
        leg_positions = [(-2.4, -1.1, 0.5), (2.4, -1.1, 0.5), (-2.4, 1.1, 0.5), (2.4, 1.1, 0.5)]
        for idx, pos in enumerate(leg_positions):
            bpy.ops.mesh.primitive_cube_add(size=0.2, location=pos)
            leg = bpy.context.object
            leg.scale[2] = 5  # Height
            leg.name = f'Leg {idx + 1}'
            leg.data.materials.append(wood_material)

# Instantiate the table
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
