# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_Blender_code_to_make_dog_bed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a Blender code to make dog bed

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the bed
bed_material = bpy.data.materials.new(name='BedMaterial')
bed_material.diffuse_color = (0.4, 0.2, 0.1, 1)  # Darker brown

# Function to add a cube with specified parameters
def add_cube(name, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=2, location=location)
    cube = bpy.context.object
    cube.scale = scale
    cube.name = name
    cube.data.materials.append(bed_material)
    return cube

# Create the bed base
add_cube('BedBase', (0, 0, 0.1), (1.5, 1, 0.1))

# Define edge dimensions
height_of_edges = 0.2
thickness_of_edges = 0.1

# Generate edges around the bed
add_cube('FrontEdge', (0, 1 - thickness_of_edges, height_of_edges / 2), (1.5, thickness_of_edges, height_of_edges))
add_cube('BackEdge', (0, -(1 - thickness_of_edges), height_of_edges / 2), (1.5, thickness_of_edges, height_of_edges))
add_cube('LeftEdge', (1.5 - thickness_of_edges, 0, height_of_edges / 2), (thickness_of_edges, 1, height_of_edges))
add_cube('RightEdge', (-(1.5 - thickness_of_edges), 0, height_of_edges / 2), (thickness_of_edges, 1, height_of_edges))


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
