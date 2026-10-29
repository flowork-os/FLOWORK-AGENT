# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_script__generate_abstract_sculpture" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender script, generate abstract sculpture.

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sculpture
material_sculpture = bpy.data.materials.new(name="Sculpture Material")
material_sculpture.diffuse_color = (0.5, 0.5, 0.5, 1)  # Medium gray

# Function to create a torus with specified parameters

def create_torus(location, major_radius, minor_radius, rotation, name):
    bpy.ops.mesh.primitive_torus_add(align='WORLD', location=location, major_radius=major_radius, minor_radius=minor_radius, rotation=rotation)
    torus = bpy.context.object
    torus.name = name
    torus.data.materials.append(material_sculpture)
    return torus

# Function to create a cylinder with specified parameters

def create_cylinder(location, radius, depth, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material_sculpture)
    return cylinder

# Create the base
create_cylinder(location=(0, 0, 0.1), radius=1, depth=0.2, name="Base")

# Create flowing shapes using toruses
create_torus(location=(0, 0, 1), major_radius=0.5, minor_radius=0.1, rotation=(0, 0, math.pi/4), name="Shape 1")
create_torus(location=(0, 0, 2), major_radius=0.4, minor_radius=0.1, rotation=(0, math.pi/4, 0), name="Shape 2")
create_torus(location=(0, 0, 3), major_radius=0.3, minor_radius=0.1, rotation=(math.pi/4, 0, 0), name="Shape 3")
create_torus(location=(0, 0, 4), major_radius=0.2, minor_radius=0.1, rotation=(0, 0, 0), name="Shape 4")

# Create connecting rods
create_cylinder(location=(0, 0, 1.5), radius=0.05, depth=1, name="Rod 1")
create_cylinder(location=(0, 0, 2.5), radius=0.05, depth=1, name="Rod 2")
create_cylinder(location=(0, 0, 3.5), radius=0.05, depth=1, name="Rod 3")


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
