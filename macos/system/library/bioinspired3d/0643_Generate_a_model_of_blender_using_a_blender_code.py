# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_blender_using_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of blender using a blender code

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set up materials for the model
material_dark = bpy.data.materials.new(name="Dark Material")
material_dark.diffuse_color = (0.2, 0.2, 0.2, 1)
material_light = bpy.data.materials.new(name="Light Material")
material_light.diffuse_color = (0.8, 0.8, 0.8, 0.3)
material_red = bpy.data.materials.new(name="Red Material")
material_red.diffuse_color = (0.8, 0.1, 0.1, 1)

# Create the main components of the model
base = bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
base_obj = bpy.context.object
base_obj.name = "Base"
base_obj.data.materials.append(material_dark)

container = bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=2, location=(0, 0, 1.5))
container_obj = bpy.context.object
container_obj.name = "Container"
container_obj.data.materials.append(material_light)

# Create buttons with a consistent pattern
for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(0.5 * (i - 1), 0.9, 0.25))
    button_object = bpy.context.object
    button_object.name = f"Control Button {i + 1}"
    button_object.data.materials.append(material_red)


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
