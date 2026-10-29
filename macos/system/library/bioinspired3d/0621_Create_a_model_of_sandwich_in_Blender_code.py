# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Create_a_model_of_sandwich_in_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Create a model of sandwich in Blender code

import bpy

# Remove existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a function to add materials

def add_material(name, rgba):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = rgba
    return mat

# Create materials for different sandwich components
bread_mat = add_material('Bread', (0.96, 0.87, 0.70, 1))
lettuce_mat = add_material('Lettuce', (0.13, 0.55, 0.13, 1))
tomato_mat = add_material('Tomato', (0.89, 0.15, 0.07, 1))
cheese_mat = add_material('Cheese', (1.0, 0.83, 0.0, 1))

# Function to create a cube with specified properties

def create_cube(name, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale[2] = scale
    cube.data.materials.append(material)

# Create the sandwich layers in sequence
create_cube('Bottom Bread', (0, 0, 0), 0.1, bread_mat)
create_cube('Lettuce', (0, 0, 0.2), 0.05, lettuce_mat)
create_cube('Tomato', (0, 0, 0.3), 0.05, tomato_mat)
create_cube('Cheese', (0, 0, 0.4), 0.05, cheese_mat)
create_cube('Top Bread', (0, 0, 0.6), 0.1, bread_mat)


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
