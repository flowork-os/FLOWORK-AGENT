# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_code_that_makes_a_model_of_pet_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender code that makes a model of pet bowl

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_bowl = bpy.data.materials.new(name='MaterialBowl')
material_bowl.diffuse_color = (0.8, 0.5, 0.2, 1)  # Light brown tone

class Bowl:
    def __init__(self, location):
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=location)
        self.object = bpy.context.object
        self.object.data.materials.append(material_bowl)

bowl_left = Bowl((-1.5, 0, 0))
bowl_left.object.name = 'BowlLeft'

bowl_right = Bowl((1.5, 0, 0))
bowl_right.object.name = 'BowlRight'

bpy.ops.mesh.primitive_cube_add(size=5, location=(0, 0, -0.25))
base_object = bpy.context.object
base_object.name = 'BaseBlock'
base_object.scale = (1, 0.5, 0.1)
base_object.data.materials.append(material_bowl)


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
