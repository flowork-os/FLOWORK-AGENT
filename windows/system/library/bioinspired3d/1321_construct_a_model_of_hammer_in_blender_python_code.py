# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, construct_a_model_of_hammer_in_blender_python_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: construct a model of hammer in blender python code

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
metal_material = bpy.data.materials.new(name='Metallic')
metal_material.diffuse_color = (0.6, 0.6, 0.6, 1)
wood_material = bpy.data.materials.new(name='Wooden')
wood_material.diffuse_color = (0.5, 0.2, 0.1, 1)

# Function to create a cube for the hammer head

def create_hammer_head():
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0.25))
    head = bpy.context.object
    head.name = 'Hammer_Head'
    head.scale[0] = 1.5
    head.data.materials.append(metal_material)

# Function to create the handle

def create_handle():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(0, 0, -1))
    handle = bpy.context.object
    handle.name = 'Hammer_Handle'
    handle.data.materials.append(wood_material)

# Create the hammer components
create_hammer_head()
create_handle()


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
