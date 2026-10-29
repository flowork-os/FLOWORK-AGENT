# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_script_generate_formal_top_hat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender script generate formal top hat

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definition for the hat
material_black = bpy.data.materials.new(name='MaterialBlack')
material_black.diffuse_color = (0, 0, 0, 1)  # Black color

# Create the top hat using functional programming

def add_cylinder(radius, height, position, mat_name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    obj = bpy.context.object
    obj.data.materials.append(bpy.data.materials[mat_name])
    return obj

# Creating the main parts of the top hat
hat_body = add_cylinder(1, 2, (0, 0, 1), 'MaterialBlack')
hat_body.name = 'TopHatBody'

hat_brim = add_cylinder(1.5, 0.1, (0, 0, 0), 'MaterialBlack')
hat_brim.name = 'TopHatBrim'


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
