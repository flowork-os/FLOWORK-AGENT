# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_that_makes_floor_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code that makes floor lamp.

import bpy

# Clear existing objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
metal_material = bpy.data.materials.new(name="Metallic")
metal_material.diffuse_color = (0.5, 0.5, 0.5, 1)
shade_material = bpy.data.materials.new(name="Light Shade")
shade_material.diffuse_color = (1, 1, 1, 1)

# Function to create a mesh object
def create_mesh(primitive_type, **kwargs):
    if primitive_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(**kwargs)
    elif primitive_type == 'cone':
        bpy.ops.mesh.primitive_cone_add(**kwargs)

# Create the stand
create_mesh('cylinder', radius=0.05, depth=2, location=(0, 0, 1))
stand_obj = bpy.context.object
stand_obj.name = "Lamp Stand"
stand_obj.data.materials.append(metal_material)

# Create the base
create_mesh('cylinder', radius=0.5, depth=0.1, location=(0, 0, 0.05))
base_obj = bpy.context.object
base_obj.name = "Lamp Base"
base_obj.data.materials.append(metal_material)

# Create the lampshade
create_mesh('cone', radius1=0.4, radius2=0.1, depth=0.6, location=(0, 0, 2.3))
lampshade_obj = bpy.context.object
lampshade_obj.name = "Lamp Shade"
lampshade_obj.data.materials.append(shade_material)


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
