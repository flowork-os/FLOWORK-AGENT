# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_code__build_travel_umbrella" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender code, build travel umbrella.

import bpy
import math

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create black and gray materials
black_material = bpy.data.materials.new(name='BlackMaterial')
black_material.diffuse_color = (0.01, 0.01, 0.01, 1)
gray_material = bpy.data.materials.new(name='GrayMaterial')
gray_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Adding mesh components
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.5, radius2=0, depth=0.1, location=(0, 0, 1.5))
cone = bpy.context.object
cone.name = 'Canopy'
cone.data.materials.append(black_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.5, location=(0, 0, 0.75))
cylinder = bpy.context.object
cylinder.name = 'Shaft'
cylinder.data.materials.append(gray_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.3, location=(0, 0, 0.15))
handle_cylinder = bpy.context.object
handle_cylinder.name = 'Handle'
handle_cylinder.data.materials.append(black_material)

bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.02, location=(0, -0.2, 0.15), rotation=(math.pi/2, 0, 0))
torus = bpy.context.object
torus.name = 'Strap'
torus.data.materials.append(black_material)


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
