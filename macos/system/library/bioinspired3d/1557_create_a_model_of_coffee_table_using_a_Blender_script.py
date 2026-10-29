# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_coffee_table_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of coffee table using a Blender script

import bpy

# Clear the existing scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood_finish = bpy.data.materials.new(name='Wood Finish')
wood_finish.diffuse_color = (0.55, 0.27, 0.07, 1)  # Warm brown hue

# Create the table using an object-oriented approach
class Table:
    def __init__(self, leg_height, leg_radius):
        self.leg_height = leg_height
        self.leg_radius = leg_radius
        self.legs = []

    def create_table_top(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
        top = bpy.context.object
        top.scale = (2, 1, 0.1)
        top.data.materials.append(wood_finish)

    def create_leg(self, position):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.leg_radius, depth=self.leg_height, location=position)
        leg = bpy.context.object
        leg.data.materials.append(wood_finish)
        self.legs.append(leg)

# Instantiate the table
my_table = Table(leg_height=0.5, leg_radius=0.05)
my_table.create_table_top()
leg_positions = [(-1.9, -0.9, my_table.leg_height / 2), (1.9, -0.9, my_table.leg_height / 2), (-1.9, 0.9, my_table.leg_height / 2), (1.9, 0.9, my_table.leg_height / 2)]
for pos in leg_positions:
    my_table.create_leg(pos)


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
