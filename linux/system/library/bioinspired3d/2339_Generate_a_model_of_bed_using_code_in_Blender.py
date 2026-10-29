# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_bed_using_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of bed using code in Blender

import bpy

# Clear the current mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for frame and mattress
bed_frame_material = bpy.data.materials.new(name='Frame')
bed_frame_material.diffuse_color = (0.5, 0.25, 0.1, 1)  # Brown
bed_mattress_material = bpy.data.materials.new(name='Mattress')
bed_mattress_material.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light Gray

# Function to add a cube with given parameters
def add_cube(size, position, scaling, label, mat):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube_obj = bpy.context.object
    cube_obj.scale = scaling
    cube_obj.name = label
    cube_obj.data.materials.append(mat)

# Add the bed frame, headboard, footboard, and mattress
add_cube(2, (0, 0, 0.25), (1, 2, 0.25), 'Bed Frame', bed_frame_material)
add_cube(2, (0, -2, 0.75), (1, 0.1, 0.75), 'Headboard', bed_frame_material)
add_cube(2, (0, 2, 0.5), (1, 0.1, 0.5), 'Footboard', bed_frame_material)
add_cube(2, (0, 0, 0.75), (0.95, 1.95, 0.2), 'Mattress', bed_mattress_material)


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
