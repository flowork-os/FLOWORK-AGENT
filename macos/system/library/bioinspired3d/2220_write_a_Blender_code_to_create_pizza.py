# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_to_create_pizza" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code to create pizza

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

mat_crust = bpy.data.materials.new(name="Crust")
mat_crust.diffuse_color = (0.76, 0.60, 0.42, 1)
mat_sauce = bpy.data.materials.new(name="Sauce")
mat_sauce.diffuse_color = (0.8, 0.1, 0.1, 1)
mat_cheese = bpy.data.materials.new(name="Cheese")
mat_cheese.diffuse_color = (1, 0.9, 0.5, 1)
mat_pepperoni = bpy.data.materials.new(name="Pepperoni")
mat_pepperoni.diffuse_color = (0.6, 0.1, 0.1, 1)

class Pizza:
    def __init__(self):
        self.base = None
        self.sauce = None
        self.cheese = None

    def create_layer(self, radius, depth, location, name, material):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        layer = bpy.context.object
        layer.name = name
        layer.data.materials.append(material)
        return layer

    def build(self):
        self.base = self.create_layer(1, 0.1, (0, 0, 0), "Pizza Base", mat_crust)
        self.sauce = self.create_layer(0.95, 0.02, (0, 0, 0.06), "Sauce", mat_sauce)
        self.cheese = self.create_layer(0.9, 0.02, (0, 0, 0.08), "Cheese", mat_cheese)

pizza = Pizza()
pizza.build()

pepperoni_locations = [
    (0.3, 0.3), (-0.3, 0.3), (0.3, -0.3), (-0.3, -0.3),
    (0.6, 0), (-0.6, 0), (0, 0.6), (0, -0.6)
]
for idx, loc in enumerate(pepperoni_locations):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.02, location=(loc[0], loc[1], 0.1))
    pepperoni = bpy.context.object
    pepperoni.name = f"Pepperoni Slice {idx + 1}"
    pepperoni.data.materials.append(mat_pepperoni)

bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = pizza.base
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=1, radius2=0, depth=0.2, location=(0, 0, 0.1), rotation=(0, 0, math.pi / 8))
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
