# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_dog_bed_in_code_in_Blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make dog bed in code in Blender

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
brown_material = bpy.data.materials.new(name="Brown Bed Material")
brown_material.diffuse_color = (0.55, 0.27, 0.07, 1)
light_gray_material = bpy.data.materials.new(name="Light Gray Cushion Material")
light_gray_material.diffuse_color = (0.8, 0.8, 0.8, 1)

# Function to create a mesh object

def create_mesh(shape, params, location, material):
    if shape == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=params[0], depth=params[1], location=location)
    elif shape == 'torus':
        bpy.ops.mesh.primitive_torus_add(major_radius=params[0], minor_radius=params[1], location=location)
    obj = bpy.context.object
    obj.data.materials.append(material)
    return obj

# Create components of the bed
bed_base = create_mesh('cylinder', (1.5, 0.2), (0, 0, 0), brown_material)
bed_base.name = "Bed Base"
raised_edges = create_mesh('torus', (1.5, 0.2), (0, 0, 0.2), brown_material)
raised_edges.name = "Raised Edges"
cushion = create_mesh('cylinder', (1.3, 0.15), (0, 0, 0.1), light_gray_material)
cushion.name = "Cushion"


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
