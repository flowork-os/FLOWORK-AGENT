# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_coffee_table_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of coffee table using Blender code

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize a wood material
material_wood = bpy.data.materials.new(name='WoodFinish')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)  # Wood-like color

# Create the table as an object-oriented approach
class Table:
    def __init__(self):
        self.create_tabletop()
        self.create_legs()

    def create_tabletop(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.4))
        self.tabletop = bpy.context.object
        self.tabletop.scale = (0.5, 1, 0.05)
        self.tabletop.name = 'Tabletop'
        self.tabletop.data.materials.append(material_wood)

    def create_legs(self):
        leg_positions = [(-0.45, -0.95, 0.2), (0.45, -0.95, 0.2), (-0.45, 0.95, 0.2), (0.45, 0.95, 0.2)]
        for i, pos in enumerate(leg_positions):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.4, location=pos)
            leg = bpy.context.object
            leg.name = f'Leg_{i + 1}'
            leg.data.materials.append(material_wood)

# Instantiate the Table class to create the model
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
