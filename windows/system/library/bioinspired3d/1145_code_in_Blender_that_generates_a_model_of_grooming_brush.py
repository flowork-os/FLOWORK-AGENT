# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_generates_a_model_of_grooming_brush" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that generates a model of grooming brush.

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for different parts of the brush
mat_handle = bpy.data.materials.new(name='Handle')
mat_handle.diffuse_color = (0.15, 0.15, 0.15, 1)  # Dark gray
mat_bristles = bpy.data.materials.new(name='Bristles')
mat_bristles.diffuse_color = (0.85, 0.85, 0.85, 1)  # Light gray

# Create the brush components
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.0, location=(0, 0, 0.5))
handle_obj = bpy.context.object
handle_obj.name = 'BrushHandle'
handle_obj.data.materials.append(mat_handle)

bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 0, 1.3))
head_obj = bpy.context.object
head_obj.name = 'BrushHead'
head_obj.data.materials.append(mat_handle)

# Loop to create bristles
for ix in range(5):
    for jx in range(5):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.3, location=(ix * 0.1 - 0.2, jx * 0.1 - 0.2, 1.5))
        bristle_obj = bpy.context.object
        bristle_obj.name = f'Bristle_{ix}_{jx}'
        bristle_obj.data.materials.append(mat_bristles)


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
