# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_code_to_make_water_bottle" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender code to make water bottle.

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the bottle and cap
bottle_mat = bpy.data.materials.new(name='BottleMaterial')
bottle_mat.diffuse_color = (0.25, 0.55, 0.85, 1)  # Soft blue
cap_mat = bpy.data.materials.new(name='CapMaterial')
cap_mat.diffuse_color = (0.15, 0.15, 0.15, 1)  # Dark gray

# Create the bottle body
bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.5, location=(0, 0, 0.75))
bottle = bpy.context.object
bottle.name = 'BottleBody'
bottle.data.materials.append(bottle_mat)

# Create the neck of the bottle
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.3, location=(0, 0, 1.65))
bottle_neck = bpy.context.object
bottle_neck.name = 'BottleNeck'
bottle_neck.data.materials.append(bottle_mat)

# Create the bottle cap
bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.2, location=(0, 0, 1.85))
cap = bpy.context.object
cap.name = 'Cap'
cap.data.materials.append(cap_mat)


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
