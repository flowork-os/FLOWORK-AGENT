# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_for_constructing_syringe" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code for constructing syringe.

import bpy
import math

# Clear existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a cylinder with a material

def create_cylinder(radius, depth, location, name, color):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    material = bpy.data.materials.new(name=name + 'Material')
    material.diffuse_color = color
    obj.data.materials.append(material)
    return obj

# Create the main barrel
barrel_color = (0.8, 0.8, 0.8, 1)
barrel = create_cylinder(0.1, 2.0, (0, 0, 1.0), 'Barrel', barrel_color)

# Create the plunger above the barrel
plunger_color = (0.6, 0.6, 0.6, 1)
plunger = create_cylinder(0.08, 2.1, (0, 0, 1.05), 'Plunger', plunger_color)

# Create the needle below the barrel
needle_color = (0.7, 0.7, 0.7, 1)
needle = create_cylinder(0.01, 0.5, (0, 0, -0.25), 'Needle', needle_color)

# Material for measurement markings
markings_color = (0.0, 0.0, 0.0, 1)
markings_material = bpy.data.materials.new(name='MarkingsMaterial')
markings_material.diffuse_color = markings_color

# Create measurement markings
for index in range(1, 10):
    bpy.ops.mesh.primitive_plane_add(size=0.02, location=(0.11, 0, 0.2 * index))
    marking = bpy.context.object
    marking.name = f'Marking_{index}'
    marking.data.materials.append(markings_material)
    marking.rotation_euler = (math.pi / 2, 0, 0)
    marking.location = (0.11, 0, 0.2 * index)


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
