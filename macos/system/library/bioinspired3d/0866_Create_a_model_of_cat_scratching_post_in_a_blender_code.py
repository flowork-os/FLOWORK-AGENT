# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_cat_scratching_post_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of cat scratching post in a blender code

import bpy

# Remove all existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize a new material for the structure
material_wood = bpy.data.materials.new(name='MaterialWood')
material_wood.diffuse_color = (0.55, 0.27, 0.07, 1)  # Brown color for wood

# Create a class for the wooden structure
class WoodenStructure:
    def __init__(self):
        self.create_post()
        self.create_base()
        self.create_platform()

    def create_post(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=2, location=(0, 0, 1))
        post = bpy.context.object
        post.name = 'Post'
        post.data.materials.append(material_wood)

    def create_base(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.4, depth=0.1, location=(0, 0, 0.05))
        base = bpy.context.object
        base.name = 'Base'
        base.data.materials.append(material_wood)

    def create_platform(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.05, location=(0, 0, 2.025))
        platform = bpy.context.object
        platform.name = 'Platform'
        platform.data.materials.append(material_wood)

# Instantiate the wooden structure
WoodenStructure()


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
