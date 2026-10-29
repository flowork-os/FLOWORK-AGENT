# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_python_code_build_a_model_of_formal_top_hat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender python code build a model of formal top hat.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a black material for the hat
black_material = bpy.data.materials.new(name='BlackMaterial')
black_material.diffuse_color = (0, 0, 0, 1)  # Pure black

# Class to represent a Top Hat
class TopHat:
    def __init__(self, body_radius, body_depth, brim_radius, brim_depth):
        self.body_radius = body_radius
        self.body_depth = body_depth
        self.brim_radius = brim_radius
        self.brim_depth = brim_depth
        self.create_hat()

    def create_hat(self):
        self.create_body()
        self.create_brim()

    def create_body(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.body_radius, depth=self.body_depth, location=(0, 0, self.body_depth / 2))
        body = bpy.context.object
        body.name = 'HatBody'
        body.data.materials.append(black_material)

    def create_brim(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.brim_radius, depth=self.brim_depth, location=(0, 0, 0))
        brim = bpy.context.object
        brim.name = 'HatBrim'
        brim.data.materials.append(black_material)

# Instantiate a Top Hat
hat = TopHat(body_radius=1, body_depth=2, brim_radius=1.5, brim_depth=0.1)


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
