# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_python_blender_code_generate_a_model_of_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using python blender code generate a model of bird feeder

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood_mat = bpy.data.materials.new(name='WoodMaterial')
wood_mat.diffuse_color = (0.55, 0.27, 0.07, 1)  # Wood-like color

# Class to handle the creation of building components
class BuildingComponent:
    @staticmethod
    def create_cube(size, location, name):
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
        cube = bpy.context.object
        cube.name = name
        cube.scale[2] = 0.1  # Flatten the cube
        cube.data.materials.append(wood_mat)
        return cube

# Create platform and roof using the class method
BuildingComponent.create_cube(2, (0, 0, 0), 'FlatPlatform')
BuildingComponent.create_cube(2.5, (0, 0, 1.5), 'FlatRoof')

# Create supports at specified locations
support_coords = [(-0.9, -0.9, 0.75), (0.9, -0.9, 0.75), (-0.9, 0.9, 0.75), (0.9, 0.9, 0.75)]
for coord in support_coords:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.5, location=coord)
    support_object = bpy.context.object
    support_object.name = 'ColumnSupport'
    support_object.data.materials.append(wood_mat)


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
