# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_Blender_Python_script__make_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With Blender Python script, make a model of blender

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
light_gray = bpy.data.materials.new(name="Light Gray")
light_gray.diffuse_color = (0.8, 0.8, 0.8, 1)
dark_gray = bpy.data.materials.new(name="Dark Gray")
dark_gray.diffuse_color = (0.1, 0.1, 0.1, 1)
red = bpy.data.materials.new(name="Red")
red.diffuse_color = (1, 0, 0, 1)
medium_gray = bpy.data.materials.new(name="Medium Gray")
medium_gray.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the base, container, and lid using the helper function
base = create_cylinder(1.2, 0.4, (0, 0, 0.2), "Base", dark_gray)
container = create_cylinder(1, 3, (0, 0, 2), "Container", light_gray)
lid = create_cylinder(1.05, 0.2, (0, 0, 3.6), "Lid", light_gray)

# Create the blade base
bpy.ops.mesh.primitive_cone_add(radius1=0.1, radius2=0, depth=0.2, location=(0, 0, 0.1))
blade_base = bpy.context.object
blade_base.name = "Blade Base"
blade_base.data.materials.append(medium_gray)

# Generate blades
for index in range(4):
    angle = math.pi / 2 * index
    bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0.3, 0.2))
    blade = bpy.context.object
    blade.name = f"Blade {index + 1}"
    blade.rotation_euler = (0, angle, 0)
    blade.data.materials.append(medium_gray)

# Create the control panel
bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 1.2, 0.4))
control_panel = bpy.context.object
control_panel.name = "Control Panel"
control_panel.data.materials.append(dark_gray)

# Create buttons
for index in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(-0.2 + index * 0.2, 1.25, 0.5))
    button = bpy.context.object
    button.name = f"Button {index + 1}"
    button.data.materials.append(red)


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
