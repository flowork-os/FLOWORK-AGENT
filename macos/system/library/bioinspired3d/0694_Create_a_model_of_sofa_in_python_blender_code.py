# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_sofa_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of sofa in python blender code

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material creation for sofa and cushions
sofa_material = bpy.data.materials.new(name='SofaMaterial')
sofa_material.diffuse_color = (0.5, 0.25, 0.1, 1)

cushion_material = bpy.data.materials.new(name='CushionMaterial')
cushion_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Class to handle sofa components
class SofaComponent:
    def __init__(self, name, size, location, scale, material):
        self.name = name
        self.size = size
        self.location = location
        self.scale = scale
        self.material = material
        self.create_component()

    def create_component(self):
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=self.location)
        obj = bpy.context.object
        obj.name = self.name
        obj.scale = self.scale
        obj.data.materials.append(self.material)

# Create seat, backrest, armrests, legs, cushions
SofaComponent('Seat', 2, (0, 0, 0.5), (2, 1, 0.2), sofa_material)
SofaComponent('Backrest', 2, (0, -0.9, 1.1), (2, 0.2, 0.6), sofa_material)

for armrest_side in [-1, 1]:
    SofaComponent(f'Armrest_{armrest_side + 2}', 2, (armrest_side * 1.9, 0, 0.8), (0.2, 1, 0.6), sofa_material)

for leg_index in range(4):
    leg_x = 1.8 * (leg_index % 2) - 0.9
    leg_y = 0.8 * (leg_index // 2) - 0.4
    SofaComponent(f'Leg_{leg_index + 1}', 0.2, (leg_x, leg_y, 0.1), (0.1, 0.1, 0.1), sofa_material)

for cushion_index in range(3):
    cushion_x = 1.2 * (cushion_index - 1)
    SofaComponent(f'SeatCushion_{cushion_index + 1}', 1, (cushion_x, 0, 0.9), (0.6, 0.9, 0.2), cushion_material)

for back_cushion_index in range(3):
    back_cushion_x = 1.2 * (back_cushion_index - 1)
    SofaComponent(f'BackCushion_{back_cushion_index + 1}', 1, (back_cushion_x, -0.9, 1.4), (0.6, 0.2, 0.4), cushion_material)


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
