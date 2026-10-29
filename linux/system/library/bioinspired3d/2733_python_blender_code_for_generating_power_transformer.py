# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_generating_power_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for generating power transformer.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions for the model components
core_material = bpy.data.materials.new(name='CoreMaterial')
core_material.diffuse_color = (0.6, 0.6, 0.6, 1)  # Lighter gray for the core
coil_material = bpy.data.materials.new(name='CoilMaterial')
coil_material.diffuse_color = (1, 0.4, 0, 1)  # Different shade of orange for the coils
terminal_material = bpy.data.materials.new(name='TerminalMaterial')
terminal_material.diffuse_color = (0, 0, 0, 1)  # Black for terminals

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Create the core
create_cylinder(0.3, 2, (0, 0, 0), 'Core', core_material)

# Function to create a torus

def create_torus(major_radius, minor_radius, location, name, material):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Create the coils
for index in range(2):
    position_z = 0.5 * (index * 2 - 1)
    create_torus(0.4, 0.05, (0, 0, position_z), f'Coil_{index + 1}', coil_material)

# Create the terminals
for index in range(2):
    position_x = 0.2 * (index * 2 - 1)
    create_cylinder(0.05, 0.2, (position_x, 0, 1.1), f'Terminal_{index + 1}', terminal_material)


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
