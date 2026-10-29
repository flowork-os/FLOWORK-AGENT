# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_bird_cage_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate bird cage using python blender code

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

metal_material = bpy.data.materials.new(name="MetallicMaterial")
metal_material.diffuse_color = (0.7, 0.7, 0.7, 1)  # Bright metallic finish

def create_mesh_object(mesh_type, params, name):
    if mesh_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=params[0], depth=params[1], location=params[2])
    elif mesh_type == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=params[0], location=params[1])
    elif mesh_type == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=params[0], location=params[1])
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(metal_material)
    return obj

base_mesh = create_mesh_object('cylinder', (1, 0.1, (0, 0, 0)), "Base")

for index in range(16):
    angle_rad = (2 * math.pi / 16) * index
    x_pos = math.cos(angle_rad)
    y_pos = math.sin(angle_rad)
    create_mesh_object('cylinder', (0.05, 2, (x_pos, y_pos, 1)), f"VerticalBar_{index + 1}")

create_mesh_object('sphere', (1, (0, 0, 2)), "Dome")
dome_object = bpy.context.object

dome_object.scale[2] = 0.5  # Flatten the dome

create_mesh_object('cube', (0.5, (1, 0, 1)), "SideDoor")
door_object = bpy.context.object

door_object.scale[2] = 1.5  # Scale to make it taller
door_object.rotation_euler[2] = math.pi / 2  # Rotate for vertical orientation
door_object.location[0] = 1.05  # Adjust door position
door_object.location[2] = 1  # Center vertically


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
