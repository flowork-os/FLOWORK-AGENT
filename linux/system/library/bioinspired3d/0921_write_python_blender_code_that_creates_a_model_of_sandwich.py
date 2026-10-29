# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_python_blender_code_that_creates_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write python blender code that creates a model of sandwich

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for sandwich components
materials = {
    'Bread': (0.96, 0.87, 0.70, 1),
    'Lettuce': (0.13, 0.55, 0.13, 1),
    'Tomato': (0.89, 0.15, 0.07, 1),
    'Cheese': (1.0, 0.83, 0.0, 1),
    'Meat': (0.55, 0.27, 0.07, 1)
}

# Function to create a layer of food

def create_layer(name, size, location, scale, material_color):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    layer = bpy.context.object
    layer.name = name
    layer.scale[2] = scale
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = material_color
    layer.data.materials.append(mat)
    return layer

# Create each layer of the sandwich
create_layer('Bottom Bread', 2, (0, 0, 0), 0.1, materials['Bread'])
create_layer('Lettuce', 1.8, (0, 0, 0.2), 0.05, materials['Lettuce'])
create_layer('Tomato', 1.8, (0, 0, 0.3), 0.05, materials['Tomato'])
create_layer('Cheese', 1.8, (0, 0, 0.4), 0.05, materials['Cheese'])
create_layer('Meat', 1.8, (0, 0, 0.5), 0.1, materials['Meat'])
create_layer('Top Bread', 2, (0, 0, 0.7), 0.1, materials['Bread'])


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
