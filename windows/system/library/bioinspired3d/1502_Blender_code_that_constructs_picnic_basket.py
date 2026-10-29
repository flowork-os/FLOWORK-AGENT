# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_that_constructs_picnic_basket" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code that constructs picnic basket

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize the material for the basket
basket_material = bpy.data.materials.new(name='BasketColor')
basket_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Brown

# Class to handle basket components
class BasketComponent:
    def __init__(self, size, location, name, scale):
        self.size = size
        self.location = location
        self.name = name
        self.scale = scale
        self.create()

    def create(self):
        bpy.ops.mesh.primitive_cube_add(size=self.size, location=self.location)
        obj = bpy.context.object
        obj.name = self.name
        obj.scale = self.scale
        obj.data.materials.append(basket_material)

# Create the basket base
base = BasketComponent(2, (0, 0, 0.5), 'BasketBase', (1, 1, 0.5))
# Create the basket lid
lid = BasketComponent(2, (0, 0, 1.25), 'BasketLid', (1, 1, 0.1))

# Create the handle using a torus
bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.05, location=(0, 0, 1.5), rotation=(1.57, 0, 0))
handle = bpy.context.object
handle.name = 'BasketHandle'
handle.data.materials.append(basket_material)

# Create the lock mechanism
lock = BasketComponent(0.2, (0, 1.1, 1.1), 'Lock', (1, 1, 1))


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
