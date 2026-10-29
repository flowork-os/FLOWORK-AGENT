# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_script__make_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender script, make a model of blender

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the model
mat_base = bpy.data.materials.new(name="Dark Material")
mat_base.diffuse_color = (0.4, 0.4, 0.4, 1)

mat_button = bpy.data.materials.new(name="Bright Red")
mat_button.diffuse_color = (1, 0.2, 0.2, 1)

mat_jar = bpy.data.materials.new(name="Frosted White")
mat_jar.diffuse_color = (1, 1, 1, 0.3)

# Generate the base of the jar
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
base_model = bpy.context.object
base_model.name = "Jar Base"
base_model.data.materials.append(mat_base)

# Generate the jar
bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=2, location=(0, 0, 1.5))
jar_model = bpy.context.object
jar_model.name = "Jar Container"
jar_model.data.materials.append(mat_jar)

# Create buttons in a loop
for i in range(3):
    button_pos_x = -0.5 + i * 0.5
    bpy.ops.mesh.primitive_cube_add(size=0.2, location=(button_pos_x, 0.9, 0.15))
    button_model = bpy.context.object
    button_model.name = f"Control Button {i + 1}"
    button_model.data.materials.append(mat_button)


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
