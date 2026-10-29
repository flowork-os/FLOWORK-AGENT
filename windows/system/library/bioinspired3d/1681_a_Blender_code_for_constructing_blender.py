# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_for_constructing_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code for constructing blender.

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
material_base = bpy.data.materials.new(name="Material Base")
material_base.diffuse_color = (0.3, 0.3, 0.3, 1)
material_container = bpy.data.materials.new(name="Material Container")
material_container.diffuse_color = (0.9, 0.9, 0.9, 0.4)
material_button = bpy.data.materials.new(name="Material Button")
material_button.diffuse_color = (0.9, 0.2, 0.2, 1)
material_lid = bpy.data.materials.new(name="Material Lid")
material_lid.diffuse_color = (0.3, 0.3, 0.3, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the base, container, lid, and control panel
create_cylinder(1, 0.5, (0, 0, 0.25), "Base", material_base)
create_cylinder(0.8, 1.5, (0, 0, 1.25), "Container", material_container)
create_cylinder(0.85, 0.1, (0, 0, 2.05), "Lid", material_lid)

# Create the control panel
bpy.ops.mesh.primitive_cube_add(size=0.4, location=(0, 1, 0.25))
control_panel = bpy.context.object
control_panel.name = "Control Panel"
control_panel.data.materials.append(material_base)

# Create buttons using a loop
for index in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(-0.2 + index * 0.15, 1.1, 0.25))
    button = bpy.context.object
    button.name = f"Button {index + 1}"
    button.data.materials.append(material_button)


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
