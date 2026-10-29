# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_code_that_creates_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender code that creates transformer.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create material for the central part
central_material = bpy.data.materials.new(name='Central Material')
central_material.diffuse_color = (0.1, 0.1, 0.1, 1)  # Darker gray

# Create material for the surrounding rings
ring_material = bpy.data.materials.new(name='Ring Material')
ring_material.diffuse_color = (0.9, 0.6, 0.3, 1)  # Brighter copper-like color

# Function to create the core

def create_core():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.0, location=(0, 0, 0))
    core_object = bpy.context.object
    core_object.name = 'Central Core'
    core_object.data.materials.append(central_material)
    return core_object

# Function to create coils

def create_coils():
    for index in range(3):
        height = -0.3 + index * 0.3
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(0, 0, height), major_radius=0.35, minor_radius=0.05)
        coil_object = bpy.context.object
        coil_object.name = f'Coil Ring {index + 1}'
        coil_object.data.materials.append(ring_material)

# Execute functions to build the model
create_core()
create_coils()


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
