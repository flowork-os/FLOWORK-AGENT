# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_travel_umbrella_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of travel umbrella in a Blender script

import bpy
import math

# Remove all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for use
mat_black = bpy.data.materials.new(name='MatBlack')
mat_black.diffuse_color = (0.01, 0.01, 0.01, 1)
mat_gray = bpy.data.materials.new(name='MatGray')
mat_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Create the canopy as a cone
bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.5, radius2=0, depth=0.1, location=(0, 0, 1.5))
canopy_object = bpy.context.object
canopy_object.name = 'Canopy'
canopy_object.data.materials.append(mat_black)

# Create the shaft using a cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.5, location=(0, 0, 0.75))
shaft_object = bpy.context.object
shaft_object.name = 'Shaft'
shaft_object.data.materials.append(mat_gray)

# Create the handle as another cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.3, location=(0, 0, 0.15))
handle_object = bpy.context.object
handle_object.name = 'Handle'
handle_object.data.materials.append(mat_black)

# Add the strap with a torus
bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.02, location=(0, -0.2, 0.15), rotation=(math.pi/2, 0, 0))
strap_object = bpy.context.object
strap_object.name = 'Strap'
strap_object.data.materials.append(mat_black)


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
