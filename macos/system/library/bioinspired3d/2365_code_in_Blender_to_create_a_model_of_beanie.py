# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_to_create_a_model_of_beanie" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender to create a model of beanie

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the beanie
beanie_material = bpy.data.materials.new(name='BeanieMaterial')
beanie_material.diffuse_color = (0.5, 0.1, 0.1, 1)  # Dark red shade

# Function to create a sphere with a specific scale
def create_sphere(location, scale_factors):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=location)
    obj = bpy.context.object
    obj.scale = scale_factors
    return obj

# Generate the beanie shape
beanie_shape = create_sphere((0, 0, 1), (1, 1, 0.6))
beanie_shape.name = 'Beanie'
beanie_shape.data.materials.append(beanie_material)

# Function to create a brim using a torus
def create_brim(location):
    bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.2, location=location)
    return bpy.context.object

# Create the brim of the beanie
brim_shape = create_brim((0, 0, 0.6))
brim_shape.name = 'Brim'
brim_shape.data.materials.append(beanie_material)


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
