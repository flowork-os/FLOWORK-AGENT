# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_python_code_to_make_a_model_of_screwdriver" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender python code to make a model of screwdriver.

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Materials for different parts
handle_col = bpy.data.materials.new(name='HandleColor')
handle_col.diffuse_color = (1.0, 0.0, 0.0, 1)  # Pure red for handle
shaft_col = bpy.data.materials.new(name='ShaftColor')
shaft_col.diffuse_color = (0.4, 0.4, 0.4, 1)  # Medium gray for shaft

# Add Handle
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.0, location=(0, 0, 0.5))
handle_obj = bpy.context.object
handle_obj.name = 'HandleObject'
handle_obj.data.materials.append(handle_col)

# Add Shaft
bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=2.0, location=(0, 0, -1.0))
shaft_obj = bpy.context.object
shaft_obj.name = 'ShaftObject'
shaft_obj.data.materials.append(shaft_col)

# Add Flat Tip
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, -2.05))
tip_obj = bpy.context.object

tip_obj.name = 'TipObject'
tip_obj.scale[1] = 0.02  # Flatten the cube

# Assign shaft color to the tip

tip_obj.data.materials.append(shaft_col)


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
