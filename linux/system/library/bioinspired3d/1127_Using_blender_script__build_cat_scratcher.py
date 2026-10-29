# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_blender_script__build_cat_scratcher" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using blender script, build cat scratcher.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the worn appearance
material_worn = bpy.data.materials.new(name="Material Worn")
material_worn.diffuse_color = (0.5, 0.3, 0.2, 1)

# Class to create and manage the structures
class CatFurniture:
    def __init__(self, material):
        self.material = material

    def create_base(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, -0.5))
        base = bpy.context.object
        base.name = "Base"
        base.data.materials.append(self.material)

    def create_post(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=3, location=(0, 0, 1))
        post = bpy.context.object
        post.name = "Scratching Post"
        post.data.materials.append(self.material)

    def create_worn_surface(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.32, depth=2.8, location=(0, 0, 1))
        worn_surface = bpy.context.object
        worn_surface.name = "Worn Scratching Surface"
        worn_surface.data.materials.append(self.material)

    def create_top(self):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 2.5))
        top = bpy.context.object
        top.name = "Top Platform"
        top.data.materials.append(self.material)

# Instantiate the CatFurniture class and create the objects
cat_furniture = CatFurniture(material_worn)
cat_furniture.create_base()
cat_furniture.create_post()
cat_furniture.create_worn_surface()
cat_furniture.create_top()


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
