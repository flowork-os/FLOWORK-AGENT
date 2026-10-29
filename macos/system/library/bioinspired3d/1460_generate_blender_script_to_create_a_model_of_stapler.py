# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_script_to_create_a_model_of_stapler" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender script to create a model of stapler.

import bpy

# Start by clearing the mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with different colors
material_stapler_body = bpy.data.materials.new(name='Stapler Base Color')
material_stapler_body.diffuse_color = (0.3, 0.3, 0.3, 1)  # Medium gray
material_stapler_lever = bpy.data.materials.new(name='Stapler Arm Color')
material_stapler_lever.diffuse_color = (0.7, 0.7, 0.7, 1)  # Soft gray

# Adding the stapler body and lever using a functional approach
def add_stapler_parts():
    # Create the body
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    body_part = bpy.context.object
    body_part.name = 'Stapler Base'
    body_part.scale = (1, 0.3, 0.2)
    body_part.data.materials.append(material_stapler_body)

    # Create the lever
    bpy.ops.mesh.primitive_cube_add(size=1.8, location=(0, 0, 0.3))
    lever_part = bpy.context.object
    lever_part.name = 'Stapler Arm'
    lever_part.scale = (1, 0.25, 0.1)
    lever_part.data.materials.append(material_stapler_lever)

add_stapler_parts()


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
