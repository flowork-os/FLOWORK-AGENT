# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_for_building_a_model_of_bird_cage" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code for building a model of bird cage

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

gray_material = bpy.data.materials.new(name="Gray Material")
gray_material.diffuse_color = (0.5, 0.5, 0.5, 1)

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.1, location=(0, 0, 0))
base_cylinder = bpy.context.object
base_cylinder.name = "Base"
base_cylinder.data.materials.append(gray_material)

def create_bars(count):
    for index in range(count):
        angle_offset = (2 * math.pi / count) * index
        x_pos = math.cos(angle_offset)
        y_pos = math.sin(angle_offset)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(x_pos, y_pos, 1))
        bar = bpy.context.object
        bar.name = f"Bar {index + 1}"
        bar.data.materials.append(gray_material)

create_bars(12)

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 2))
dome_shape = bpy.context.object
dome_shape.name = "Dome"
dome_shape.scale[2] = 0.5
dome_shape.data.materials.append(gray_material)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
mesh_data = dome_shape.data
for vertex in mesh_data.vertices:
    if vertex.co.z < 0:
        vertex.select = True
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.delete(type='VERT')
bpy.ops.object.mode_set(mode='OBJECT')


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
