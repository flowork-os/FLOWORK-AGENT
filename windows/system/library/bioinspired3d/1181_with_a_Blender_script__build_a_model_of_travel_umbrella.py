# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_a_Blender_script__build_a_model_of_travel_umbrella" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with a Blender script, build a model of travel umbrella

import bpy
import math

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
material_black = bpy.data.materials.new(name='Material_Black')
material_black.diffuse_color = (0.01, 0.01, 0.01, 1)
material_gray = bpy.data.materials.new(name='Material_Gray')
material_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to add a cone for the canopy

def add_cone(location):
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.5, radius2=0, depth=0.1, location=location)
    cone = bpy.context.object
    cone.name = 'Canopy'
    cone.data.materials.append(material_black)
    return cone

# Function to add a cylinder

def add_cylinder(location, radius, depth, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    cylinder = bpy.context.object
    cylinder.name = name
    cylinder.data.materials.append(material)
    return cylinder

# Create the canopy
add_cone((0, 0, 1.5))

# Create the telescopic shaft
add_cylinder((0, 0, 0.75), 0.05, 1.5, 'Shaft', material_gray)

# Create the handle
add_cylinder((0, 0, 0.15), 0.1, 0.3, 'Handle', material_black)

# Create the strap using a torus
bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.02, location=(0, -0.2, 0.15), rotation=(math.pi/2, 0, 0))
strap = bpy.context.object
strap.name = 'Strap'
strap.data.materials.append(material_black)


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
