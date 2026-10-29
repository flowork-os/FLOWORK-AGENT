# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_Blender_Python_script_to_create_syringe" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate Blender Python script to create syringe

import bpy
import math

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Class to handle the creation of objects
class ObjectCreator:
    def __init__(self):
        pass

    @staticmethod
    def add_cylinder(radius, depth, position, name, color):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
        obj = bpy.context.object
        obj.name = name
        mat = bpy.data.materials.new(name=name + '_Material')
        mat.diffuse_color = color
        obj.data.materials.append(mat)

# Instantiate the object creator
creator = ObjectCreator()

# Create the barrel
creator.add_cylinder(0.1, 2.0, (0, 0, 1.0), 'Barrel', (0.8, 0.8, 0.8, 1))
# Create the plunger
creator.add_cylinder(0.08, 2.1, (0, 0, 1.05), 'Plunger', (0.6, 0.6, 0.6, 1))
# Create the needle
creator.add_cylinder(0.01, 0.5, (0, 0, -0.25), 'Needle', (0.7, 0.7, 0.7, 1))

# Create markings material
markings_mat = bpy.data.materials.new(name='MarkingsMaterial')
markings_mat.diffuse_color = (0.0, 0.0, 0.0, 1)

# Generate measurement markings
for i in range(1, 10):
    bpy.ops.mesh.primitive_plane_add(size=0.02, location=(0.11, 0, 0.2 * i))
    marking = bpy.context.object
    marking.name = f'Marking_{i}'
    marking.data.materials.append(markings_mat)
    marking.rotation_euler = (math.pi / 2, 0, 0)


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
