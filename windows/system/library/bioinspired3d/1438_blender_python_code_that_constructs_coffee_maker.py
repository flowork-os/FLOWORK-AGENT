# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_constructs_coffee_maker" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that constructs coffee maker

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for different parts of the model
material_body = bpy.data.materials.new(name="Material_Body")
material_body.diffuse_color = (0.2, 0.2, 0.2, 1)
material_spout = bpy.data.materials.new(name="Material_Spout")
material_spout.diffuse_color = (0.2, 0.2, 0.2, 1)
material_handle = bpy.data.materials.new(name="Material_Handle")
material_handle.diffuse_color = (0.2, 0.2, 0.2, 1)
material_lid = bpy.data.materials.new(name="Material_Lid")
material_lid.diffuse_color = (0.2, 0.2, 0.2, 1)

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the body of the model
body = create_cylinder(1, 2, (0, 0, 1), "Body", material_body)

# Create the spout
create_cylinder(0.1, 0.5, (1.1, 0, 1.5), "Spout", material_spout)

# Function to create a torus

def create_torus(major_radius, minor_radius, location, rotation, name, material):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the handle
handle = create_torus(0.5, 0.1, (-1.5, 0, 1.5), (math.pi/2, 0, 0), "Handle", material_handle)

# Create the lid
create_cylinder(1.1, 0.1, (0, 0, 2.05), "Lid", material_lid)


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
