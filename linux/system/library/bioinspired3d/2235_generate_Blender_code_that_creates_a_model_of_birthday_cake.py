# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_that_creates_a_model_of_birthday_cake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code that creates a model of birthday cake

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the cake
cake_texture = bpy.data.materials.new(name='Cake Texture')
cake_texture.diffuse_color = (0.9, 0.7, 0.5, 1)

# Class to represent a cake layer
class CakeLayer:
    def __init__(self, radius, depth, z_position, name):
        self.radius = radius
        self.depth = depth
        self.z_position = z_position
        self.name = name
        self.create_layer()

    def create_layer(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.radius, depth=self.depth, location=(0, 0, self.z_position))
        layer = bpy.context.object
        layer.name = self.name
        layer.data.materials.append(cake_texture)

# Instantiate cake layers
CakeLayer(1.5, 0.5, 0.25, 'Bottom Layer')
CakeLayer(1.2, 0.5, 0.75, 'Middle Layer')
CakeLayer(0.9, 0.5, 1.25, 'Top Layer')


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
