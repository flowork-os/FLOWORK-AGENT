# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_code_in_Blender_that_creates_a_model_of_hat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write code in Blender that creates a model of hat.

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set up material properties for the hat
brown_material = bpy.data.materials.new(name='BrownMaterial')
brown_material.diffuse_color = (0.4, 0.2, 0.1, 1)  # Darker shade of brown

# Create the hat using an object-oriented approach
class Hat:
    def __init__(self, brim_radius, brim_depth, top_radius, top_depth):
        self.brim_radius = brim_radius
        self.brim_depth = brim_depth
        self.top_radius = top_radius
        self.top_depth = top_depth

    def create_brim(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.brim_radius, depth=self.brim_depth, location=(0, 0, 0))
        brim = bpy.context.object
        brim.name = 'HatBrim'
        brim.data.materials.append(brown_material)

    def create_top(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.top_radius, depth=self.top_depth, location=(0, 0, 0.55))
        top = bpy.context.object
        top.name = 'HatTop'
        top.data.materials.append(brown_material)

# Instantiate and create the hat
my_hat = Hat(1.5, 0.1, 0.75, 1)
my_hat.create_brim()
my_hat.create_top()


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
