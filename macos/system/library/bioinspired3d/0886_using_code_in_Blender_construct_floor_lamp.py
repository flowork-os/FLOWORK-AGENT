# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_code_in_Blender_construct_floor_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using code in Blender construct floor lamp.

import bpy
import math

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
metal_material = bpy.data.materials.new(name="Metal Material")
metal_material.diffuse_color = (0.5, 0.5, 0.5, 1)
shade_material = bpy.data.materials.new(name="Shade Material")
shade_material.diffuse_color = (1, 1, 1, 1)

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the stand
stand_obj = create_cylinder(0.05, 2, (0, 0, 1), "Lamp Stand", metal_material)

# Create the base
base_obj = create_cylinder(0.5, 0.1, (0, 0, 0.05), "Lamp Base", metal_material)

# Create the shade
shade_obj = create_cylinder(0.6, 0.8, (0, 0, 2.4), "Lamp Shade", shade_material)

# Create the drum
create_cylinder(0.4, 0.2, (0, 0, 2.7), "Lamp Drum", metal_material)

# Create the foot switch
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0.5, 0, 0.05))
foot_switch_obj = bpy.context.object
foot_switch_obj.name = "Lamp Foot Switch"
foot_switch_obj.data.materials.append(metal_material)


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
