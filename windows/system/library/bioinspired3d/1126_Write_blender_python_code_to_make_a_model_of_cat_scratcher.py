# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_python_code_to_make_a_model_of_cat_scratcher" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender python code to make a model of cat scratcher

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material to simulate a weathered surface
weathered_material = bpy.data.materials.new(name="Weathered Material")
weathered_material.diffuse_color = (0.5, 0.3, 0.2, 1)  # A faded brown shade

# Function to add a cube with a specified size and location

def add_cube(size, location, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.data.materials.append(material)
    return cube

# Function to add a cylinder with specified parameters

def add_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)
    return cylinder

# Create the base cube
base_cube = add_cube(2, (0, 0, -0.5), "Base Cube", weathered_material)

# Create the scratching post
scratching_post = add_cylinder(0.3, 3, (0, 0, 1), "Scratching Post", weathered_material)

# Create the worn scratching surface
worn_surface_cylinder = add_cylinder(0.32, 2.8, (0, 0, 1), "Worn Scratching Surface", weathered_material)

# Create the top platform
platform = add_cube(1, (0, 0, 2.5), "Top Platform", weathered_material)


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
