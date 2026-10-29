# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_trash_can_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of trash can using a Blender script

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the trash can
trash_can_material = bpy.data.materials.new(name='TrashCanMaterial')
trash_can_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to add a trash can component
def add_trash_can_component(radius, depth, position, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    component = bpy.context.object
    component.name = name
    component.data.materials.append(trash_can_material)

# Create the main body and lid of the trash can
add_trash_can_component(1, 2, (0, 0, 1), 'Trash Can Body')
add_trash_can_component(1.05, 0.1, (0, 0, 2.05), 'Trash Can Lid')


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
