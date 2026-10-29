# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_for_generating_a_model_of_hammer_vs__mallet" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script for generating a model of hammer vs. mallet

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Materials for the hammer and mallet
mat_metal = bpy.data.materials.new(name='Metal')
mat_metal.diffuse_color = (0.65, 0.65, 0.65, 1)
mat_wood = bpy.data.materials.new(name='Wood')
mat_wood.diffuse_color = (0.55, 0.3, 0.1, 1)

# Create the hammer components
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(-1, 0, 0))
handle_hammer = bpy.context.object
handle_hammer.name = 'Hammer_Handle'
handle_hammer.data.materials.append(mat_wood)

bpy.ops.mesh.primitive_cube_add(size=0.3, location=(-1, 0, 0.5))
head_hammer = bpy.context.object
head_hammer.name = 'Hammer_Head'
head_hammer.data.materials.append(mat_metal)

# Create the mallet components
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(1, 0, 0))
handle_mallet = bpy.context.object
handle_mallet.name = 'Mallet_Handle'
handle_mallet.data.materials.append(mat_wood)

bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.4, location=(1, 0, 0.5), rotation=(1.5708, 0, 0))
head_mallet = bpy.context.object
head_mallet.name = 'Mallet_Head'
head_mallet.data.materials.append(mat_metal)


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
