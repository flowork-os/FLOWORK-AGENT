# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_python_blender_code_to_create_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate python blender code to create a model of blender

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize materials with descriptive names
base_material = bpy.data.materials.new(name="Base Material")
base_material.diffuse_color = (0.5, 0.5, 0.5, 1)  # Medium gray
jug_material = bpy.data.materials.new(name="Jug Material")
jug_material.diffuse_color = (0.7, 0.7, 0.7, 0.4)  # Light gray with transparency
button_material = bpy.data.materials.new(name="Button Material")
button_material.diffuse_color = (0.15, 0.15, 0.15, 1)  # Darker button color

# Create the base object
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
base_object = bpy.context.object
base_object.name = "Base"
base_object.data.materials.append(base_material)

# Create the jug object
bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=1.5, location=(0, 0, 1.25))
jug_object = bpy.context.object
jug_object.name = "Jug"
jug_object.data.materials.append(jug_material)

# Create the control panel
bpy.ops.mesh.primitive_cube_add(size=0.6, location=(0, 0.9, 0.4))
control_panel = bpy.context.object
control_panel.name = "Control Panel"
control_panel.scale[0] = 1.5
control_panel.scale[2] = 0.2
control_panel.data.materials.append(base_material)

# Define button positions
button_locations = [(-0.3, 0.9, 0.45), (0, 0.9, 0.45), (0.3, 0.9, 0.45)]
for i, loc in enumerate(button_locations):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=loc)
    button_obj = bpy.context.object
    button_obj.name = f"Button {i + 1}"
    button_obj.data.materials.append(button_material)


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
