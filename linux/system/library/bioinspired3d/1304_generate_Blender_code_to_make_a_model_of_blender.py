# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_to_make_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code to make a model of blender

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with descriptive names
base_material = bpy.data.materials.new(name='Base Material')
base_material.diffuse_color = (0.2, 0.2, 0.2, 1)
pitcher_material = bpy.data.materials.new(name='Pitcher Material')
pitcher_material.diffuse_color = (0.8, 0.8, 0.8, 0.5)
lid_material = bpy.data.materials.new(name='Lid Material')
lid_material.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the base, pitcher, lid, and center cap
base = create_cylinder(1, 0.5, (0, 0, 0.25), 'Base', base_material)
pitcher = create_cylinder(0.9, 2, (0, 0, 1.5), 'Pitcher', pitcher_material)
lid = create_cylinder(0.95, 0.1, (0, 0, 2.55), 'Lid', lid_material)
center_cap = create_cylinder(0.3, 0.1, (0, 0, 2.65), 'Center Cap', lid_material)

# Create measurement markings using cubes
for index in range(1, 5):
    bpy.ops.mesh.primitive_cube_add(size=0.05, location=(0.95, 0, 0.5 * index + 0.5))
    marking = bpy.context.object
    marking.name = f'Marking {index}'
    marking.data.materials.append(lid_material)


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
