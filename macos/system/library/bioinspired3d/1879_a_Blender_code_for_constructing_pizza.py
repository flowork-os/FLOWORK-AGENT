# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_constructing_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for constructing pizza.

import bpy

def clear_scene():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

clear_scene()

def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

crust = create_material('Crust', (0.76, 0.60, 0.42, 1))
sauce = create_material('Sauce', (0.89, 0.15, 0.07, 1))
cheese = create_material('Cheese', (1.0, 0.83, 0.0, 1))
pepperoni = create_material('Pepperoni', (0.6, 0.1, 0.1, 1))

def create_pizza_component(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    component = bpy.context.object
    component.name = name
    component.data.materials.append(material)

create_pizza_component(1, 0.1, (0, 0, 0), 'Pizza Base', crust)
create_pizza_component(0.95, 0.02, (0, 0, 0.06), 'Tomato Sauce', sauce)
create_pizza_component(0.9, 0.02, (0, 0, 0.08), 'Cheese', cheese)

pepperoni_positions = [(0.5, 0.5), (-0.5, 0.5), (0.5, -0.5), (-0.5, -0.5), (0.5, 0), (-0.5, 0), (0, 0.5), (0, -0.5)]
for i, (x, y) in enumerate(pepperoni_positions):
    create_pizza_component(0.1, 0.02, (x, y, 0.1), f'Pepperoni Slice {i + 1}', pepperoni)


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
