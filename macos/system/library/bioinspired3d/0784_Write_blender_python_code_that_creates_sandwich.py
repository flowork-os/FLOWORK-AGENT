# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_python_code_that_creates_sandwich" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender python code that creates sandwich.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a function to create a sandwich component

def add_sandwich_component(name, position, scale_factor, rgba):
    bpy.ops.mesh.primitive_cube_add(size=2, location=position)
    component = bpy.context.object
    component.name = name
    component.scale[2] = scale_factor
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = rgba
    component.data.materials.append(material)

# Create the sandwich layers
add_sandwich_component('Base Bread', (0, 0, 0), 0.1, (0.96, 0.87, 0.70, 1))
add_sandwich_component('Leafy Greens', (0, 0, 0.2), 0.05, (0.13, 0.55, 0.13, 1))
add_sandwich_component('Red Slice', (0, 0, 0.3), 0.05, (0.8, 0.1, 0.1, 1))
add_sandwich_component('Yellow Slice', (0, 0, 0.4), 0.05, (1, 0.9, 0.5, 1))
add_sandwich_component('Pink Slice', (0, 0, 0.5), 0.05, (0.91, 0.59, 0.48, 1))
add_sandwich_component('Top Bread', (0, 0, 0.7), 0.1, (0.96, 0.87, 0.70, 1))


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
