# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_coffee_table_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make coffee table using a Blender code

import bpy

# Clear the existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the table
material_wood = bpy.data.materials.new(name='Wooden Material')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)  # Deep brown shade

# Class to represent a table
class Table:
    def __init__(self):
        self.legs = []

    def create_top(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.75))
        top = bpy.context.object
        top.scale[0] = 1.5
        top.scale[1] = 0.75
        top.scale[2] = 0.1
        top.name = 'Table Top'
        top.data.materials.append(material_wood)

    def create_legs(self):
        leg_height = 0.75
        leg_radius = 0.05
        leg_positions = [(-1.4, -0.7, leg_height / 2), (1.4, -0.7, leg_height / 2), (-1.4, 0.7, leg_height / 2), (1.4, 0.7, leg_height / 2)]
        for i, pos in enumerate(leg_positions):
            bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=leg_height, location=pos)
            leg = bpy.context.object
            leg.name = f'Leg {i + 1}'
            leg.data.materials.append(material_wood)
            self.legs.append(leg)

    def create_shelf(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.25))
        shelf = bpy.context.object
        shelf.scale[0] = 1.4
        shelf.scale[1] = 0.7
        shelf.scale[2] = 0.05
        shelf.name = 'Lower Shelf'
        shelf.data.materials.append(material_wood)

# Instantiate and build the table
my_table = Table()
my_table.create_top()
my_table.create_legs()
my_table.create_shelf()


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
