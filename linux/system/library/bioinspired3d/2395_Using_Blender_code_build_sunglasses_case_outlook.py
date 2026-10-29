# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_Blender_code_build_sunglasses_case_outlook" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using Blender code build sunglasses case outlook.

import bpy

# Clear the mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize a material for the case
case_material = bpy.data.materials.new(name='Case Material')
case_material.diffuse_color = (0.2, 0.2, 0.2, 1)  # Dark gray color

# Object-oriented approach to create case parts
class CasePart:
    def __init__(self, location, scale, name):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=location)
        self.obj = bpy.context.object
        self.obj.name = name
        self.obj.scale = scale
        self.obj.data.materials.append(case_material)

# Create the main body and bottom part
main_body = CasePart((0, 0, 0), (2, 1, 0.5), 'Main Body')
bottom_part = CasePart((0, 0, -0.5), (2, 1, 0.25), 'Bottom Part')

# Select and join the parts
bpy.ops.object.select_all(action='DESELECT')
main_body.obj.select_set(True)
bottom_part.obj.select_set(True)
bpy.context.view_layer.objects.active = main_body.obj
bpy.ops.object.join()


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
