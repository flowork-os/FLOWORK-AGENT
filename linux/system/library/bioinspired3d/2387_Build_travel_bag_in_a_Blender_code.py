# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Build_travel_bag_in_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Build travel bag in a Blender code

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the bag and its components
material_bag = bpy.data.materials.new(name='MaterialBag')
material_bag.diffuse_color = (0.1, 0.1, 0.1, 1)

material_zipper = bpy.data.materials.new(name='MaterialZipper')
material_zipper.diffuse_color = (0.8, 0.8, 0.8, 1)

material_handle = bpy.data.materials.new(name='MaterialHandle')
material_handle.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to create a cube
def create_cube(size, location, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.data.materials.append(material)
    return cube

# Create the main compartment of the bag
main_compartment = create_cube(2, (0, 0, 0), 'MainCompartment', material_bag)
main_compartment.scale = (1, 0.5, 0.5)

# Create the zipper
zipper = create_cube(0.1, (0, 0, 0.55), 'Zipper', material_zipper)
zipper.scale = (1, 0.05, 0.05)

# Function to create handles
def create_handle(x):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1, location=(x, 0, 0.5), rotation=(0, 1.57, 0))
    handle = bpy.context.object
    handle.data.materials.append(material_handle)
    handle.name = f'Handle {int((x + 0.8) / 1.6 + 1)}'

# Create both handles
for i in range(2):
    create_handle(0.8 * (i * 2 - 1))


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
