# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_blender_code_to_make_a_model_of_grooming_brush" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a blender code to make a model of grooming brush.

import bpy

# Remove existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Materials for the brush
material_handle = bpy.data.materials.new(name='MaterialHandle')
material_handle.diffuse_color = (0.3, 0.3, 0.3, 1)  # Medium gray
material_bristle = bpy.data.materials.new(name='MaterialBristle')
material_bristle.diffuse_color = (0.7, 0.7, 0.7, 1)  # Grayish color

# Creating brush components in an object-oriented way
class Brush:
    def __init__(self):
        self.create_handle()
        self.create_head()
        self.create_bristles()

    def create_handle(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.0, location=(0, 0, 0.5))
        handle = bpy.context.object
        handle.name = 'BrushHandle'
        handle.data.materials.append(material_handle)

    def create_head(self):
        bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 0, 1.3))
        head = bpy.context.object
        head.name = 'BrushHead'
        head.data.materials.append(material_handle)

    def create_bristles(self):
        for x in range(5):
            for y in range(5):
                bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.3, location=(x * 0.1 - 0.2, y * 0.1 - 0.2, 1.5))
                bristle = bpy.context.object
                bristle.name = f'Bristle_{x}_{y}'
                bristle.data.materials.append(material_bristle)

# Instantiate the brush
Brush()


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
