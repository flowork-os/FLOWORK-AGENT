# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_bed_using_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create bed using python blender code

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the bed components
frame_material = bpy.data.materials.new(name='Bed Frame Material')
frame_material.diffuse_color = (0.5, 0.25, 0.1, 1)  # Brown
mattress_material = bpy.data.materials.new(name='Bed Mattress Material')
mattress_material.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light Gray

# Function to create a cube with specified parameters
def create_cube(size, location, scale, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.name = name
    cube.data.materials.append(material)

# Construct the bed frame, headboard, footboard, and mattress
create_cube(2, (0, 0, 0.25), (1, 2, 0.25), 'Bed Frame', frame_material)
create_cube(2, (0, -2, 0.75), (1, 0.1, 0.75), 'Headboard', frame_material)
create_cube(2, (0, 2, 0.5), (1, 0.1, 0.5), 'Footboard', frame_material)
create_cube(2, (0, 0, 0.75), (0.95, 1.95, 0.2), 'Mattress', mattress_material)


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
