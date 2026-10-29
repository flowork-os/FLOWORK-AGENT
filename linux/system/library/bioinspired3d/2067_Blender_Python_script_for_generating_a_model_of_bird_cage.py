# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_generating_a_model_of_bird_cage" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for generating a model of bird cage

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

metallic_material = bpy.data.materials.new(name="Metallic")
metallic_material.diffuse_color = (0.7, 0.7, 0.7, 1)

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(metallic_material)
    return obj

base_cylinder = create_cylinder(1, 0.1, (0, 0, 0), "Base")

bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 2))
top_sphere = bpy.context.object
top_sphere.name = "Top"
top_sphere.scale[2] = 0.5
top_sphere.data.materials.append(metallic_material)

bar_count = 16
for index in range(bar_count):
    angle_rad = index * (2 * math.pi / bar_count)
    x_coord = math.cos(angle_rad)
    y_coord = math.sin(angle_rad)
    create_cylinder(0.05, 2, (x_coord, y_coord, 1), f"Bar {index + 1}")

bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1, 0, 1))
door_cube = bpy.context.object
door_cube.name = "Door"
door_cube.data.materials.append(metallic_material)

perch_cylinder = create_cylinder(0.05, 1.5, (0, 0, 0.5), "Perch")
perch_cylinder.rotation_euler = (0, math.pi/2, 0)

bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.05, location=(0, 0, 2.5))
hook_torus = bpy.context.object
hook_torus.name = "Hook"
hook_torus.data.materials.append(metallic_material)


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
