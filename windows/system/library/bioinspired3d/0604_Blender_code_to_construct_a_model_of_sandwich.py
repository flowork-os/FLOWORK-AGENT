# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_to_construct_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code to construct a model of sandwich

import bpy

# Function to clear the scene

def clear_scene():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

# Clear the existing objects
clear_scene()

# Function to create a colored cube layer

def create_cube_layer(size, position, name, color):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    cube = bpy.context.object
    cube.scale[2] = 0.1 if 'Bread' in name else 0.05
    cube.name = name
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = color
    cube.data.materials.append(material)

# Define colors for the sandwich components
colors = {
    'Bread': (0.96, 0.87, 0.70, 1),
    'Lettuce': (0.13, 0.55, 0.13, 1),
    'Tomato': (0.8, 0.1, 0.1, 1),
    'Cheese': (1, 0.83, 0, 1)
}

# Create the sandwich layers
create_cube_layer(2, (0, 0, 0), 'Bottom Bread', colors['Bread'])
create_cube_layer(2, (0, 0, 0.2), 'Lettuce', colors['Lettuce'])
create_cube_layer(2, (0, 0, 0.3), 'Tomato', colors['Tomato'])
create_cube_layer(2, (0, 0, 0.4), 'Cheese', colors['Cheese'])
create_cube_layer(2, (0, 0, 0.6), 'Top Bread', colors['Bread'])


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
