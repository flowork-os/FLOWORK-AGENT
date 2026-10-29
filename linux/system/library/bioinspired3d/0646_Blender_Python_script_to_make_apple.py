# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_to_make_apple" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script to make apple.

import bpy

# Start by clearing the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the apple and stem
apple_material = bpy.data.materials.new(name='Apple Material')
apple_material.diffuse_color = (0.8, 0.1, 0.1, 1)

stem_material = bpy.data.materials.new(name='Stem Material')
stem_material.diffuse_color = (0.4, 0.2, 0.1, 1)

# Function to generate the apple

def generate_apple():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
    apple = bpy.context.object
    apple.name = 'Apple'
    apple.data.materials.append(apple_material)

# Function to generate the stem

def generate_stem():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=(0, 0, 1.25))
    stem = bpy.context.object
    stem.name = 'Stem'
    stem.data.materials.append(stem_material)

# Create the apple and stem
generate_apple()
generate_stem()


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
