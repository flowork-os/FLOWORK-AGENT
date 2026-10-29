# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_Blender_code__make_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using Blender code, make a model of blender

import bpy
import math

# Clear the mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
material_main = bpy.data.materials.new(name='MainMaterial')
material_main.diffuse_color = (0.25, 0.25, 0.25, 1)

material_transparent = bpy.data.materials.new(name='TransparentMaterial')
material_transparent.diffuse_color = (0.85, 0.85, 0.85, 0.2)

material_blade = bpy.data.materials.new(name='BladeMaterial')
material_blade.diffuse_color = (0.9, 0.9, 0.9, 1)

# Create objects using a helper function

def add_cylinder(radius, depth, position, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Base, container, lid, and cap creation
add_cylinder(1, 0.5, (0, 0, 0.25), 'BaseShape', material_main)
add_cylinder(0.8, 2, (0, 0, 1.5), 'ContainerShape', material_transparent)
add_cylinder(0.85, 0.1, (0, 0, 2.55), 'LidShape', material_main)
add_cylinder(0.2, 0.2, (0, 0, 2.65), 'CapShape', material_main)

# Create blades
bpy.ops.mesh.primitive_plane_add(size=0.5, location=(0, 0, 1))
blades_object = bpy.context.object
blades_object.name = 'BladeObject'
blades_object.data.materials.append(material_blade)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.transform.rotate(value=math.pi / 4, orient_axis='Z')
bpy.ops.object.mode_set(mode='OBJECT')

# Control panel setup
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 1, 0.25))
control_panel_object = bpy.context.object
control_panel_object.name = 'ControlPanelShape'
control_panel_object.data.materials.append(material_main)

# Adding buttons to the control panel
for index in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(-0.15 + index * 0.15, 1.1, 0.25))
    button_object = bpy.context.object
    button_object.name = f'ControlButton_{index + 1}'
    button_object.data.materials.append(material_main)


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
