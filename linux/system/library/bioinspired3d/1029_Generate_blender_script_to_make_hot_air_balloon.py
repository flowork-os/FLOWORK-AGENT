# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_script_to_make_hot_air_balloon" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender script to make hot air balloon.

import bpy

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the balloon, basket, and ropes
red_balloon_material = bpy.data.materials.new(name='Red Balloon Material')
red_balloon_material.diffuse_color = (0.8, 0.1, 0.1, 1)
brown_basket_material = bpy.data.materials.new(name='Brown Basket Material')
brown_basket_material.diffuse_color = (0.5, 0.25, 0.1, 1)
gray_rope_material = bpy.data.materials.new(name='Gray Rope Material')
gray_rope_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Function to create a balloon

def create_balloon():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 2))
    balloon_object = bpy.context.object
    balloon_object.name = 'Balloon'
    balloon_object.data.materials.append(red_balloon_material)

# Function to create a basket

def create_basket():
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0))
    basket_object = bpy.context.object
    basket_object.name = 'Basket'
    basket_object.data.materials.append(brown_basket_material)

# Function to create ropes

def create_ropes():
    positions = [(0.25, 0.25, 1), (-0.25, 0.25, 1), (0.25, -0.25, 1), (-0.25, -0.25, 1)]
    for position in positions:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=2, location=position)
        rope_object = bpy.context.object
        rope_object.name = 'Rope'
        rope_object.data.materials.append(gray_rope_material)

create_balloon()
create_basket()
create_ropes()


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
