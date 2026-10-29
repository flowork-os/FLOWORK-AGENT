# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_abstract_pattern_using_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of abstract pattern using Blender code

import bpy
import math

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material for the shapes
material = bpy.data.materials.new(name='Neutral Gray')
material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Class to handle the creation of geometric shapes
class ShapeCreator:
    @staticmethod
    def add_torus(index):
        angle = index * math.pi / 5
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(math.cos(angle), math.sin(angle), 0))
        torus = bpy.context.object
        torus.name = f'Torus_{index + 1}'
        torus.data.materials.append(material)

    @staticmethod
    def add_cylinder(index):
        angle = index * math.pi / 5
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(math.cos(angle), math.sin(angle), 0), rotation=(0, 0, angle))
        cylinder = bpy.context.object
        cylinder.name = f'Cylinder_{index + 1}'
        cylinder.data.materials.append(material)

    @staticmethod
    def add_sphere(index):
        angle = index * math.pi / 5
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(math.cos(angle), math.sin(angle), 0))
        sphere = bpy.context.object
        sphere.name = f'Sphere_{index + 1}'
        sphere.data.materials.append(material)

# Create shapes in the scene
for i in range(5):
    ShapeCreator.add_torus(i)
    ShapeCreator.add_cylinder(i)
    ShapeCreator.add_sphere(i)


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
