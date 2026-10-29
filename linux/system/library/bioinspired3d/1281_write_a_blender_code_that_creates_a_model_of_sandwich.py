# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_blender_code_that_creates_a_model_of_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a blender code that creates a model of sandwich

import bpy

# Remove all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the sandwich layers
colors = [
    (0.9, 0.7, 0.5, 1),  # Bread
    (0.2, 0.8, 0.2, 1),  # Lettuce
    (0.8, 0.1, 0.1, 1),  # Tomato
    (1, 0.9, 0.1, 1),    # Cheese
    (0.9, 0.6, 0.6, 1)   # Ham
]
material_names = ['Bottom Bread', 'Lettuce', 'Tomato', 'Cheese', 'Ham', 'Top Bread']

# Function to add a layer to the sandwich

def add_layer(name, position, mat_index):
    bpy.ops.mesh.primitive_plane_add(size=2, location=position)
    layer = bpy.context.object
    layer.name = name
    layer.data.materials.append(bpy.data.materials.new(name=material_names[mat_index]))
    layer.data.materials[-1].diffuse_color = colors[mat_index]

# Build the sandwich layers
add_layer('Bottom Bread', (0, 0, 0), 0)
add_layer('Lettuce', (0, 0, 0.15), 1)
add_layer('Tomato', (0, 0, 0.25), 2)
add_layer('Cheese', (0, 0, 0.35), 3)
add_layer('Ham', (0, 0, 0.45), 4)
add_layer('Top Bread', (0, 0, 0.6), 0)


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
