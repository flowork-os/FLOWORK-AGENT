# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_blender_code__construct_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a blender code, construct pizza

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

crust_material = bpy.data.materials.new(name="Crust Material")
crust_material.diffuse_color = (0.76, 0.60, 0.42, 1)
sauce_material = bpy.data.materials.new(name="Sauce Material")
sauce_material.diffuse_color = (0.8, 0.1, 0.1, 1)
cheese_material = bpy.data.materials.new(name="Cheese Material")
cheese_material.diffuse_color = (1, 0.9, 0.5, 1)
pepperoni_material = bpy.data.materials.new(name="Pepperoni Material")
pepperoni_material.diffuse_color = (0.6, 0.1, 0.1, 1)

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

pizza_base = create_cylinder(1, 0.1, (0, 0, 0), "Pizza Base", crust_material)
sauce_layer = create_cylinder(0.95, 0.02, (0, 0, 0.06), "Sauce Layer", sauce_material)
cheese_layer = create_cylinder(0.9, 0.02, (0, 0, 0.08), "Cheese Layer", cheese_material)

pepperoni_positions = [
    (0.3, 0.3), (-0.3, 0.3), (0.3, -0.3), (-0.3, -0.3),
    (0.6, 0), (-0.6, 0), (0, 0.6), (0, -0.6)
]

for index, position in enumerate(pepperoni_positions):
    create_cylinder(0.1, 0.02, (position[0], position[1], 0.1), f"Pepperoni Slice {index + 1}", pepperoni_material)

bpy.ops.object.select_all(action='DESELECT')
pizza_base.select_set(True)
bpy.context.view_layer.objects.active = pizza_base
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1, radius2=0, depth=0.2, location=(0, 0, 0.1), rotation=(0, 0, math.pi/8))
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.object.select_set(True)
bpy.ops.object.join()
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.intersect_boolean(operation='DIFFERENCE')
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
