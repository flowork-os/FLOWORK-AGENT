# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_bird_cage_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of bird cage using a Blender script

import bpy
import math

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material with gray color
material_gray = bpy.data.materials.new(name="Gray Material")
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Define a function to create a mesh object

def add_mesh_object(mesh_type, params, object_name):
    if mesh_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=params['radius'], depth=params['depth'], location=params['location'])
    elif mesh_type == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=params['radius'], location=params['location'])
    obj = bpy.context.object
    obj.name = object_name
    obj.data.materials.append(material_gray)
    return obj

# Create the base mesh
base_mesh = add_mesh_object('cylinder', {'radius': 1, 'depth': 0.1, 'location': (0, 0, 0)}, "Base")

# Create vertical bars in a circular arrangement
bar_total = 12
for bar_index in range(bar_total):
    theta = (2 * math.pi / bar_total) * bar_index
    coords = (math.cos(theta), math.sin(theta), 1)
    add_mesh_object('cylinder', {'radius': 0.05, 'depth': 2, 'location': coords}, f"Vertical Bar {bar_index + 1}")

# Create the dome on top
add_mesh_object('sphere', {'radius': 1, 'location': (0, 0, 2)}, "Dome")
dome_object = bpy.context.object

dome_object.scale[2] = 0.5  # Flatten the sphere to form a dome

dome_object.data.materials.append(material_gray)

# Switch to edit mode to delete the bottom half of the dome
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
mesh_data = dome_object.data
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
