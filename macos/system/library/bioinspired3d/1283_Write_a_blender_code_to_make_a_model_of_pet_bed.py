# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_blender_code_to_make_a_model_of_pet_bed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a blender code to make a model of pet bed

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the bed
bed_material = bpy.data.materials.new(name='Bed Material')
bed_material.diffuse_color = (0.6, 0.4, 0.2, 1)  # A different shade of brown

# Function to create a cylinder base

def create_base(location):
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.2, location=location)
    base_object = bpy.context.object
    base_object.name = 'Bed Base'
    base_object.data.materials.append(bed_material)
    return base_object

# Function to create a rim

def create_rim(location):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.2, location=location)
    rim_object = bpy.context.object
    rim_object.name = 'Bed Rim'
    rim_object.data.materials.append(bed_material)
    return rim_object

# Create the bed components
base = create_base((0, 0, 0))
rim = create_rim((0, 0, 0.2))


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
