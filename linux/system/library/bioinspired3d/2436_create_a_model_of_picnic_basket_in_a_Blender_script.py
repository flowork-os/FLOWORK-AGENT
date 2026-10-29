# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, create_a_model_of_picnic_basket_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: create a model of picnic basket in a Blender script

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a brown material for the basket
brown_material = bpy.data.materials.new(name='BrownBasket')
brown_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Brown tone

# Define a function to add a cube
def add_cube(size, location, name, z_scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale[2] = z_scale
    cube.data.materials.append(brown_material)

# Create the basket base
add_cube(2, (0, 0, 0.5), 'BasketBase', 0.5)
# Create the basket lid
add_cube(2, (0, 0, 1.25), 'BasketLid', 0.1)

# Create the handle as a torus
bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.05, location=(0, 0, 1.5), rotation=(1.57, 0, 0))
handle = bpy.context.object
handle.name = 'BasketHandle'
handle.data.materials.append(brown_material)

# Create the locking mechanism
add_cube(0.2, (0, 1.1, 1.1), 'Lock', 1)


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
