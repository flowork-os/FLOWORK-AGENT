# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_sofa_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate sofa in a Blender script

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define sofa material
sofa_surface = bpy.data.materials.new(name='SofaSurface')
sofa_surface.diffuse_color = (0.7, 0.1, 0.1, 1)  # New color choice

# Create the main components of the sofa
components = [
    {'name': 'Seat', 'location': (0, 0, 0.5), 'scale': (2, 1, 0.2)},
    {'name': 'Backrest', 'location': (0, -0.9, 1.2), 'scale': (2, 0.2, 1)},
    {'name': 'Armrest 1', 'location': (2, 0, 0.9), 'scale': (0.2, 1, 0.7)},
    {'name': 'Armrest 2', 'location': (-2, 0, 0.9), 'scale': (0.2, 1, 0.7)}
]

# Function to create sofa components
def build_sofa_component(component):
    bpy.ops.mesh.primitive_cube_add(size=2, location=component['location'])
    part = bpy.context.object
    part.name = component['name']
    part.scale = component['scale']
    part.data.materials.append(sofa_surface)

# Create each component
for comp in components:
    build_sofa_component(comp)


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
