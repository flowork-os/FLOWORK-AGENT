# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_a_model_of_sun_hat_using_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make a model of sun hat using blender code

import bpy
import math

# Clear the existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create and assign materials
hat_mat = bpy.data.materials.new(name='Hat Material')
hat_mat.diffuse_color = (0.7, 0.5, 0.3, 1)  # A darker brown
ribbon_mat = bpy.data.materials.new(name='Ribbon Material')
ribbon_mat.diffuse_color = (1, 0.1, 0.1, 1)  # Bright red

# Function to create a sphere with given parameters

def create_sphere(radius, location, name, material):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create brim
bpy.ops.mesh.primitive_cylinder_add(radius=2, depth=0.1, location=(0, 0, 0))
brim = bpy.context.object
brim.name = 'Brim'
brim.data.materials.append(hat_mat)

# Create crown
crown = create_sphere(1, (0, 0, 0.6), 'Crown', hat_mat)

# Create ribbon using cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1.05, depth=0.1, location=(0, 0, 0.6))
ribbon = bpy.context.object
ribbon.name = 'Ribbon'
ribbon.data.materials.append(ribbon_mat)

# Create bow loops
for x in [-0.25, 0.25]:
    bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.05, location=(x, -1.05, 0.6), rotation=(math.pi/2, 0, 0))
    loop = bpy.context.object
    loop.name = f'Loop at {x}'
    loop.data.materials.append(ribbon_mat)

# Create the knot
knot = create_sphere(0.1, (0, -1.05, 0.6), 'Knot', ribbon_mat)


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
