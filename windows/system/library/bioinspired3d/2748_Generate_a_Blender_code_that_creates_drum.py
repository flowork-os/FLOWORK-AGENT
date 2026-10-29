# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_code_that_creates_drum" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender code that creates drum.

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the drum components
material_drum_body = bpy.data.materials.new(name="Body")
material_drum_body.diffuse_color = (0.8, 0.2, 0.2, 1)
material_drum_head = bpy.data.materials.new(name="Head")
material_drum_head.diffuse_color = (0.9, 0.9, 0.9, 1)
material_sticks = bpy.data.materials.new(name="Sticks")
material_sticks.diffuse_color = (0.5, 0.25, 0.1, 1)

# Create the drum body and apply material
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1.5, location=(0, 0, 0.75))
body_object = bpy.context.object
body_object.name = "Drum Body"
body_object.data.materials.append(material_drum_body)

# Create the drumhead and apply material
bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.1, location=(0, 0, 1.5))
drumhead_object = bpy.context.object
drumhead_object.name = "Drumhead"
drumhead_object.data.materials.append(material_drum_head)

# Create drumsticks using a list of positions
positions = [(-1.2, 0, 0.75), (1.2, 0, 0.75)]
for index, position in enumerate(positions):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.5, location=position, rotation=(1.5708, 0, 0))
    stick_object = bpy.context.object
    stick_object.name = f"Drumstick {index + 1}"
    stick_object.data.materials.append(material_sticks)


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
