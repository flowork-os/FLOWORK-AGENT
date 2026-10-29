# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_a_blender_code_construct_fruit_basket" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using a blender code construct fruit basket.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

basket_color = bpy.data.materials.new(name='BrownBasket')
basket_color.diffuse_color = (0.6, 0.3, 0.1, 1)  # A lighter hue of brown

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

basket_base = create_cylinder(1, 0.2, (0, 0, 0), 'BasketBase', basket_color)
basket_walls = create_cylinder(1, 1, (0, 0, 0.6), 'BasketWalls', basket_color)

inner_wall = create_cylinder(0.9, 1.2, (0, 0, 0.6), 'InnerWall', None)

bool_mod = basket_walls.modifiers.new(name='HollowOut', type='BOOLEAN')
bool_mod.operation = 'DIFFERENCE'
bool_mod.object = inner_wall
bpy.context.view_layer.objects.active = basket_walls
bpy.ops.object.modifier_apply(modifier='HollowOut')

bpy.data.objects.remove(inner_wall, do_unlink=True)


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
