# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_Blender_Python_script_that_creates_screwdriver" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write Blender Python script that creates screwdriver

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set colors for the components
red_handle = bpy.data.materials.new(name='RedHandle')
red_handle.diffuse_color = (0.8, 0.1, 0.1, 1)  # A strong red for the handle
gray_shaft = bpy.data.materials.new(name='GrayShaft')
gray_shaft.diffuse_color = (0.4, 0.4, 0.4, 1)  # Darker gray for the shaft

# Create the Handle
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.0, location=(0, 0, 0.5))
handle_part = bpy.context.object
handle_part.name = 'HandlePart'
handle_part.data.materials.append(red_handle)

# Create the Shaft
bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=2.0, location=(0, 0, -1.0))
shaft_part = bpy.context.object
shaft_part.name = 'ShaftPart'
shaft_part.data.materials.append(gray_shaft)

# Create the Flat Tip
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, -2.05))
tip_part = bpy.context.object
tip_part.name = 'TipPart'
tip_part.scale[1] = 0.02  # Flatten the tip

# Assign material to the tip
tip_part.data.materials.append(gray_shaft)


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
