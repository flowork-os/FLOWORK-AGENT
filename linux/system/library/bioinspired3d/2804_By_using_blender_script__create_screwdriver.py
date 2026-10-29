# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_script__create_screwdriver" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender script, create screwdriver.

import bpy

# Remove all mesh objects to start fresh
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the model
red_handle = bpy.data.materials.new(name='RedHandle')
red_handle.diffuse_color = (0.7, 0.0, 0.0, 1)  # Dark red for handle
gray_shaft = bpy.data.materials.new(name='GrayShaft')
gray_shaft.diffuse_color = (0.4, 0.4, 0.4, 1)  # Darker gray for shaft

# Create a handle
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.5, location=(0, 0, 0.75))
handle_obj = bpy.context.object
handle_obj.name = 'Handle'
handle_obj.data.materials.append(red_handle)

# Create the shaft
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(0, 0, 2.25))
shaft_obj = bpy.context.object
shaft_obj.name = 'Shaft'
shaft_obj.data.materials.append(gray_shaft)

# Create the tip using a cube and scale it down
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, 3.25))
tip_obj = bpy.context.object
tip_obj.scale[2] = 0.03  # Flatten the cube

tip_obj.name = 'Tip'
tip_obj.data.materials.append(gray_shaft)


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
