# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_blender_script_to_create_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate blender script to create transformer.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the different parts
mat_body = bpy.data.materials.new(name="MaterialBody")
mat_body.diffuse_color = (0.5, 0.5, 0.5, 1)
mat_coil = bpy.data.materials.new(name="MaterialCoil")
mat_coil.diffuse_color = (0.8, 0.4, 0.1, 1)
mat_terminal = bpy.data.materials.new(name="MaterialTerminal")
mat_terminal.diffuse_color = (0.1, 0.1, 0.1, 1)

# Function to add a body

def add_body():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    body = bpy.context.object
    body.name = "BodyCube"
    body.scale = (1, 0.5, 1)
    body.data.materials.append(mat_body)

# Function to add coils

def add_coils():
    for i in range(2):
        loc_x = 1.2 * (i * 2 - 1)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1, location=(loc_x, 0, 0))
        coil = bpy.context.object
        coil.name = f"CoilPart_{i + 1}"
        coil.data.materials.append(mat_coil)

# Function to add terminals

def add_terminals():
    for i in range(2):
        loc_x = 0.5 * (i * 2 - 1)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(loc_x, 0, 1.1))
        terminal = bpy.context.object
        terminal.name = f"TerminalPart_{i + 1}"
        terminal.data.materials.append(mat_terminal)

# Call the functions to create the model
add_body()
add_coils()
add_terminals()


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
