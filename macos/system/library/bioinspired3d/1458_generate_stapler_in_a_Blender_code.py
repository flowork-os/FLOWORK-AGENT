# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_stapler_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate stapler in a Blender code

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the stapler components
body_material = bpy.data.materials.new(name='Body Material')
body_material.diffuse_color = (0.1, 0.1, 0.1, 1)  # Darker gray
lever_material = bpy.data.materials.new(name='Lever Material')
lever_material.diffuse_color = (0.9, 0.9, 0.9, 1)  # Lighter gray

# Function to create a cube with specific properties

def create_cube(name, size, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(material)
    return cube

# Create the stapler body and lever
stapler_body = create_cube('Stapler Body', 2, (0, 0, 0), (1, 0.3, 0.2), body_material)
stapler_lever = create_cube('Stapler Lever', 1.8, (0, 0, 0.3), (1, 0.25, 0.1), lever_material)


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
