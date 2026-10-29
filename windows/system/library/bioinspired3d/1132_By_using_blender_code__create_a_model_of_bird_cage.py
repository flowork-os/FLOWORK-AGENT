# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_code__create_a_model_of_bird_cage" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender code, create a model of bird cage

import bpy
import math

# Remove all mesh objects in the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the structure
material_meta = bpy.data.materials.new(name="Metallic Finish")
material_meta.diffuse_color = (0.7, 0.7, 0.7, 1)

# Function to add a mesh object

def add_mesh_object(mesh_type, params, name):
    if mesh_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=params[0], depth=params[1], location=params[2])
    elif mesh_type == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=params[0], location=params[1])
    elif mesh_type == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=params[0], location=params[1])
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material_meta)
    return obj

# Create base
base_object = add_mesh_object('cylinder', (1, 0.1, (0, 0, 0)), "Base")

# Create top
add_mesh_object('sphere', (1, (0, 0, 2)), "Top")
bpy.context.object.scale[2] = 0.5

# Create bars
for i in range(16):
    angle = i * (2 * math.pi / 16)
    x_pos = math.cos(angle)
    y_pos = math.sin(angle)
    add_mesh_object('cylinder', (0.05, 2, (x_pos, y_pos, 1)), f"Bar {i + 1}")

# Add the door
add_mesh_object('cube', (0.5, (1, 0, 1)), "Door")

# Add perch
perch = add_mesh_object('cylinder', (0.05, 1.5, (0, 0, 0.5)), "Perch")
perch.rotation_euler = (0, math.pi/2, 0)

# Add hook
add_mesh_object('torus', (0.2, 0.05, (0, 0, 2.5)), "Hook")


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
