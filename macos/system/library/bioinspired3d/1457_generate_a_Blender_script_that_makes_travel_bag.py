# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_Blender_script_that_makes_travel_bag" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a Blender script that makes travel bag.

import bpy

# Clear the scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the bag and zipper
material_dark_gray = bpy.data.materials.new(name='DarkGray')
material_dark_gray.diffuse_color = (0.1, 0.1, 0.1, 1)

material_light_gray = bpy.data.materials.new(name='LightGray')
material_light_gray.diffuse_color = (0.8, 0.8, 0.8, 1)

# Create a function to add a cube with specified properties

def add_cube(size, position, mat_name):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube = bpy.context.object
    cube.data.materials.append(mat_name)
    return cube

# Construct the main compartment
main_bag = add_cube(2, (0, 0, 0), material_dark_gray)
main_bag.scale = (1, 0.5, 0.5)
main_bag.name = 'MainBag'

# Construct the zipper
zipper_part = add_cube(0.1, (0, 0, 0.55), material_light_gray)
zipper_part.scale = (1, 0.05, 0.05)
zipper_part.name = 'ZipperPart'

# Create handles using a loop
for index in range(2):
    x_coord = 0.8 * (index * 2 - 1)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(x_coord, 0, 0.5), rotation=(0, 1.57, 0))
    handle_item = bpy.context.object
    handle_item.name = f'BagHandle_{index + 1}'
    handle_item.data.materials.append(material_dark_gray)


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
