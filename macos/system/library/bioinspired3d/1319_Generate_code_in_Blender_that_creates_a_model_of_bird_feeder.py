# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_code_in_Blender_that_creates_a_model_of_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate code in Blender that creates a model of bird feeder.

import bpy

# Remove all mesh objects to start fresh
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for wood appearance
wood_texture = bpy.data.materials.new(name='WoodTexture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)  # Simulated wood color

# Function to instantiate a cube at a specified location

def add_cube(size, position, label):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube_instance = bpy.context.object
    cube_instance.name = label
    cube_instance.scale[2] = 0.1  # Flatten the cube
    cube_instance.data.materials.append(wood_texture)

# Create the platform and roof
add_cube(2, (0, 0, 0), 'MainPlatform')
add_cube(2.5, (0, 0, 1.5), 'MainRoof')

# List of positions for the supports
support_locations = [(-0.9, -0.9, 0.75), (0.9, -0.9, 0.75), (-0.9, 0.9, 0.75), (0.9, 0.9, 0.75)]
for location in support_locations:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.5, location=location)
    support_instance = bpy.context.object
    support_instance.name = 'SupportPole'
    support_instance.data.materials.append(wood_texture)


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
