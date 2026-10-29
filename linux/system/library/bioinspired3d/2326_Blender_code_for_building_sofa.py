# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_for_building_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code for building sofa

import bpy

# Remove all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize the sofa's material
sofa_surface_material = bpy.data.materials.new(name="Sofa Surface")
sofa_surface_material.diffuse_color = (0.5, 0.1, 0.1, 1)  # Rich crimson color

# Create the sofa components using a function
def add_sofa_component(component_name, component_location, component_scale):
    bpy.ops.mesh.primitive_cube_add(size=2, location=component_location)
    component = bpy.context.object
    component.name = component_name
    component.scale = component_scale
    component.data.materials.append(sofa_surface_material)

# Build the main parts of the sofa
add_sofa_component("Sofa Base", (0, 0, 0.5), (2, 1, 0.5))
add_sofa_component("Sofa Backrest", (0, -1, 1.25), (2, 0.1, 1))

# Generate armrests on both sides
for i in range(2):
    position_x = 1.9 * (i * 2 - 1)
    add_sofa_component(f"Sofa Armrest {i + 1}", (position_x, 0, 1), (0.1, 1, 0.5))


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
