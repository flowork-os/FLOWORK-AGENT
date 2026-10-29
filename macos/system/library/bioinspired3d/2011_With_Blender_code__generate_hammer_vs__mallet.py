# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_Blender_code__generate_hammer_vs__mallet" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With Blender code, generate hammer vs. mallet.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions for the hammer and mallet
metal_material = bpy.data.materials.new(name='Metallic')
metal_material.diffuse_color = (0.75, 0.75, 0.75, 1)
wood_material = bpy.data.materials.new(name='Wooden')
wood_material.diffuse_color = (0.5, 0.25, 0.1, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Function to create a cube
def create_cube(size, location, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create Hammer Handle
hammer_handle = create_cylinder(0.05, 1, (-1, 0, 0), 'Hammer_Handle', wood_material)

# Create Hammer Head
hammer_head = create_cube(0.3, (-1, 0, 0.5), 'Hammer_Head', metal_material)

# Create Mallet Handle
mallet_handle = create_cylinder(0.05, 1, (1, 0, 0), 'Mallet_Handle', wood_material)

# Create Mallet Head
mallet_head = create_cylinder(0.2, 0.4, (1, 0, 0.5), 'Mallet_Head', metal_material)
mallet_head.rotation_euler = (1.5708, 0, 0)


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
