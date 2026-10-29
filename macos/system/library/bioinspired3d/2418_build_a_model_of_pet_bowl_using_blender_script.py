# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_pet_bowl_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of pet bowl using blender script

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

bowl_material = bpy.data.materials.new(name='BowlMaterial')
bowl_material.diffuse_color = (0.8, 0.5, 0.2, 1)  # Brownish color

def add_bowl(position):
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=position)
    current_bowl = bpy.context.object
    current_bowl.data.materials.append(bowl_material)
    return current_bowl

bowl_one = add_bowl((-1.5, 0, 0))
bowl_one.name = 'BowlOne'

bowl_two = add_bowl((1.5, 0, 0))
bowl_two.name = 'BowlTwo'

bpy.ops.mesh.primitive_cube_add(size=5, location=(0, 0, -0.25))
base_structure = bpy.context.object
base_structure.name = 'BaseStructure'
base_structure.scale = (1, 0.5, 0.1)
base_structure.data.materials.append(bowl_material)


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
