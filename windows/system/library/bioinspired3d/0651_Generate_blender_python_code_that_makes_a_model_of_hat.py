# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_python_code_that_makes_a_model_of_hat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender python code that makes a model of hat

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create material for the hat
hat_material = bpy.data.materials.new(name="Hat Material")
hat_material.diffuse_color = (0.5, 0.25, 0.1, 1)

# Create the brim using a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1.5, depth=0.1, location=(0, 0, 0))
brim_object = bpy.context.object
brim_object.name = "Brim"
brim_object.data.materials.append(hat_material)

# Create the crown using a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.75, depth=1, location=(0, 0, 0.55))
crown_object = bpy.context.object
crown_object.name = "Crown"
crown_object.data.materials.append(hat_material)


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
