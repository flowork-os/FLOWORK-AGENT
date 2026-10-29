# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_to_construct_a_model_of_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code to construct a model of transformer.

import bpy

# Reset the scene by removing all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials with different names
body_mat = bpy.data.materials.new(name="GrayMaterial")
body_mat.diffuse_color = (0.5, 0.5, 0.5, 1)
coil_mat = bpy.data.materials.new(name="OrangeMaterial")
coil_mat.diffuse_color = (0.8, 0.4, 0.1, 1)
terminal_mat = bpy.data.materials.new(name="BlackMaterial")
terminal_mat.diffuse_color = (0.1, 0.1, 0.1, 1)

# Create the body using a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
body = bpy.context.object
body.name = "CubeBody"
body.scale = (1, 0.5, 1)
body.data.materials.append(body_mat)

# Generate coils with a loop
for i in range(2):
    coil_x = 1.2 * (i * 2 - 1)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1, location=(coil_x, 0, 0))
    coil = bpy.context.object
    coil.name = f"Coil_{i + 1}"
    coil.data.materials.append(coil_mat)

# Create terminal ends
for i in range(2):
    terminal_x = 0.5 * (i * 2 - 1)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(terminal_x, 0, 1.1))
    terminal = bpy.context.object
    terminal.name = f"Terminal_{i + 1}"
    terminal.data.materials.append(terminal_mat)


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
