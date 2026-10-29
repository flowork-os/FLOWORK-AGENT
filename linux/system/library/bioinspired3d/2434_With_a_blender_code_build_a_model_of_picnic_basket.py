# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_blender_code_build_a_model_of_picnic_basket" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a blender code build a model of picnic basket

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

basket_material = bpy.data.materials.new(name='BasketMaterial')
basket_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Brown shade

def create_cube(size, location, name, scale):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(basket_material)
    return cube

basket_base = create_cube(2, (0, 0, 0.5), 'BasketBase', (1, 1, 0.5))
basket_lid = create_cube(2, (0, 0, 1.25), 'BasketLid', (1, 1, 0.1))

def create_handle(location, rotation):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.05, location=location, rotation=rotation)
    handle = bpy.context.object
    handle.name = 'BasketHandle'
    handle.data.materials.append(basket_material)

create_handle((0, 0, 1.5), (1.57, 0, 0))
create_cube(0.2, (0, 1.1, 1.1), 'LockMechanism', (1, 1, 1))


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
