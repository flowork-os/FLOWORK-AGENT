# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_code_generate_a_model_of_burger" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender code generate a model of burger

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the burger components
bun_mat = bpy.data.materials.new(name="Bun Material")
bun_mat.diffuse_color = (0.8, 0.6, 0.4, 1)
patty_mat = bpy.data.materials.new(name="Patty Material")
patty_mat.diffuse_color = (0.4, 0.2, 0.1, 1)
lettuce_mat = bpy.data.materials.new(name="Lettuce Material")
lettuce_mat.diffuse_color = (0.2, 0.8, 0.2, 1)
cheese_mat = bpy.data.materials.new(name="Cheese Material")
cheese_mat.diffuse_color = (1, 0.9, 0, 1)

# Using a class to create burger components
class BurgerComponent:
    def __init__(self, shape, params, name, material):
        self.shape = shape
        self.params = params
        self.name = name
        self.material = material
        self.create()

    def create(self):
        if self.shape == 'cylinder':
            bpy.ops.mesh.primitive_cylinder_add(radius=self.params[0], depth=self.params[1], location=self.params[2])
        elif self.shape == 'cube':
            bpy.ops.mesh.primitive_cube_add(size=self.params[0], location=self.params[1])
            obj = bpy.context.object
            obj.scale[2] = 0.05
        obj = bpy.context.object
        obj.name = self.name
        obj.data.materials.append(self.material)

# Create each component
BurgerComponent('cylinder', (1, 0.3, (0, 0, 0)), 'Bottom Bun', bun_mat)
BurgerComponent('cylinder', (0.9, 0.2, (0, 0, 0.25)), 'Patty', patty_mat)
BurgerComponent('cube', (1.8, (0, 0, 0.45)), 'Cheese', cheese_mat)
BurgerComponent('cylinder', (1, 0.1, (0, 0, 0.55)), 'Lettuce', lettuce_mat)
BurgerComponent('cylinder', (1, 0.3, (0, 0, 0.75)), 'Top Bun', bun_mat)


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
