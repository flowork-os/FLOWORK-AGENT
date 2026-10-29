# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_a_blender_code_to_create_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write a blender code to create a model of blender

import bpy

# Clear existing mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions with meaningful names
material_base = bpy.data.materials.new(name="Material Base")
material_base.diffuse_color = (0.4, 0.4, 0.4, 1)  # Slightly lighter gray
material_jug = bpy.data.materials.new(name="Material Jug")
material_jug.diffuse_color = (0.9, 0.9, 0.9, 0.6)  # Light gray with more transparency
material_button = bpy.data.materials.new(name="Material Button")
material_button.diffuse_color = (0.2, 0.2, 0.2, 1)  # Darker button color

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Create the base
create_cylinder(radius=1, depth=0.5, location=(0, 0, 0.25), name="Base", material=material_base)

# Create the jug
create_cylinder(radius=0.8, depth=1.5, location=(0, 0, 1.25), name="Jug", material=material_jug)

# Function to create a panel

def create_panel(size, location, name, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    panel = bpy.context.object
    panel.name = name
    panel.scale[0] = 1.5
    panel.scale[2] = 0.2
    panel.data.materials.append(material)

# Create the control panel
create_panel(size=0.6, location=(0, 0.9, 0.4), name="Control Panel", material=material_base)

# Create buttons at specified positions
button_coords = [(-0.3, 0.9, 0.45), (0, 0.9, 0.45), (0.3, 0.9, 0.45)]
for index, coordinates in enumerate(button_coords):
    create_panel(size=0.1, location=coordinates, name=f"Button {index + 1}", material=material_button)


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
