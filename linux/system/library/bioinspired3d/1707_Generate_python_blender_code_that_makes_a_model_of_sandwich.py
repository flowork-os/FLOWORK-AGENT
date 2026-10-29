# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_python_blender_code_that_makes_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate python blender code that makes a model of sandwich

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the sandwich layers
materials = {
    'Bread': (0.96, 0.87, 0.70, 1),
    'Lettuce': (0.13, 0.55, 0.13, 1),
    'Tomato': (0.8, 0.1, 0.1, 1),
    'Cheese': (1, 0.9, 0.5, 1),
    'Ham': (0.91, 0.59, 0.48, 1)
}

# Function to create a cube with a specific material
def create_layer(name, position, scale, color):
    bpy.ops.mesh.primitive_cube_add(size=2, location=position)
    layer = bpy.context.object
    layer.name = name
    layer.scale[2] = scale
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = color
    layer.data.materials.append(material)
    return layer

# Create sandwich layers with specified positions and scales
create_layer('Bottom Bread', (0, 0, 0), 0.1, materials['Bread'])
create_layer('Lettuce', (0, 0, 0.2), 0.05, materials['Lettuce'])
create_layer('Tomato', (0, 0, 0.3), 0.05, materials['Tomato'])
create_layer('Cheese', (0, 0, 0.4), 0.05, materials['Cheese'])
create_layer('Ham', (0, 0, 0.5), 0.05, materials['Ham'])
create_layer('Top Bread', (0, 0, 0.7), 0.1, materials['Bread'])


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
