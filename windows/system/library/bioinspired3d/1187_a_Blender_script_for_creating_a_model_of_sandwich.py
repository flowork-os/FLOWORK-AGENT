# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_for_creating_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script for creating a model of sandwich

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cube with a specific material

def create_cube(name, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube = bpy.context.object
    cube.name = name
    cube.scale = scale
    cube.data.materials.append(material)
    return cube

# Define materials for the sandwich layers
bread_material = bpy.data.materials.new(name='Bread')
bread_material.diffuse_color = (0.9, 0.7, 0.5, 1)

lettuce_material = bpy.data.materials.new(name='Lettuce')
lettuce_material.diffuse_color = (0.2, 0.8, 0.2, 1)

tomato_material = bpy.data.materials.new(name='Tomato')
tomato_material.diffuse_color = (0.8, 0.1, 0.1, 1)

cheese_material = bpy.data.materials.new(name='Cheese')
cheese_material.diffuse_color = (1, 0.9, 0.3, 1)

meat_material = bpy.data.materials.new(name='Meat')
meat_material.diffuse_color = (0.6, 0.3, 0.2, 1)

# Create sandwich layers
create_cube('Bottom Bread', (0, 0, 0), (1, 1, 0.1), bread_material)
create_cube('Lettuce', (0, 0, 0.2), (1, 1, 0.05), lettuce_material)
create_cube('Tomato', (0, 0, 0.3), (1, 1, 0.05), tomato_material)
create_cube('Cheese', (0, 0, 0.4), (1, 1, 0.05), cheese_material)
create_cube('Meat', (0, 0, 0.5), (1, 1, 0.1), meat_material)
create_cube('Top Bread', (0, 0, 0.7), (1, 1, 0.1), bread_material)


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
