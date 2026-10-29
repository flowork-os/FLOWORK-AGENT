# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_build_a_model_of_logo" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to build a model of logo.

import bpy

# Clear the scene of any mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the logo
logo_mat = bpy.data.materials.new(name='LogoMaterial')
logo_mat.diffuse_color = (0.8, 0.2, 0.2, 1)  # Red color

# Create a base for the logo
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.1, location=(0, 0, 0))
base_logo = bpy.context.object
base_logo.name = 'LogoBase'
base_logo.data.materials.append(logo_mat)

# Create the cross shape
# Adding the horizontal section
bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 0, 0.05))
horizontal_section = bpy.context.object
horizontal_section.scale = (1, 0.1, 0.1)
horizontal_section.name = 'HorizontalSection'
horizontal_section.data.materials.append(logo_mat)

# Adding the vertical section
bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 0, 0.05))
vertical_section = bpy.context.object
vertical_section.scale = (0.1, 1, 0.1)
vertical_section.name = 'VerticalSection'
vertical_section.data.materials.append(logo_mat)


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
