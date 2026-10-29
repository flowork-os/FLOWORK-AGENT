# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_create_a_model_of_coffee_table" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to create a model of coffee table.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

wood_texture = bpy.data.materials.new(name='Wood Finish')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

def add_table_top():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
    top_surface = bpy.context.object
    top_surface.scale = (2, 1, 0.1)
    top_surface.name = 'Top Surface'
    top_surface.data.materials.append(wood_texture)

def add_leg(x, y, z):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=(x, y, z))
    leg_component = bpy.context.object
    leg_component.data.materials.append(wood_texture)
    return leg_component

add_table_top()

leg_positions = [(-1.9, -0.9, 0.25), (1.9, -0.9, 0.25), (-1.9, 0.9, 0.25), (1.9, 0.9, 0.25)]
for pos in leg_positions:
    add_leg(*pos)


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
