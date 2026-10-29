# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_build_a_model_of_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to build a model of bird feeder.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material with a wood-like texture
wood_material = bpy.data.materials.new(name='WoodMaterial')
wood_material.diffuse_color = (0.55, 0.27, 0.07, 1)  # Color resembling wood

# Function to create a flat cube

def create_flat_cube(size, location, name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale[2] = 0.1  # Flatten the cube
    cube.data.materials.append(wood_material)
    return cube

# Create the base platform and roof
platform = create_flat_cube(2, (0, 0, 0), 'BasePlatform')
roof = create_flat_cube(2.5, (0, 0, 1.5), 'TopRoof')

# Define support positions and create them
support_positions = [(-0.9, -0.9, 0.75), (0.9, -0.9, 0.75), (-0.9, 0.9, 0.75), (0.9, 0.9, 0.75)]
for position in support_positions:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.5, location=position)
    support = bpy.context.object
    support.name = 'SupportColumn'
    support.data.materials.append(wood_material)


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
