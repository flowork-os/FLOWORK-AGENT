# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_Blender_code_that_creates_a_model_of_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate Blender code that creates a model of transformer

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_body = bpy.data.materials.new(name="MainBodyMaterial")
material_body.diffuse_color = (0.5, 0.5, 0.5, 1)  # Main body color
material_coil = bpy.data.materials.new(name="SpiralMaterial")
material_coil.diffuse_color = (0.8, 0.4, 0.1, 1)  # Color for coils
material_terminal = bpy.data.materials.new(name="EndMaterial")
material_terminal.diffuse_color = (0.1, 0.1, 0.1, 1)  # Color for terminals

def create_body():
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    body = bpy.context.object
    body.name = "MainBody"
    body.scale = (1, 0.5, 1)
    body.data.materials.append(material_body)

def create_coils():
    for index in range(2):
        x_position = 1.2 * (index * 2 - 1)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1, location=(x_position, 0, 0))
        coil = bpy.context.object
        coil.name = f"Spiral {index + 1}"
        coil.data.materials.append(material_coil)

def create_terminals():
    for index in range(2):
        x_position = 0.5 * (index * 2 - 1)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(x_position, 0, 1.1))
        terminal = bpy.context.object
        terminal.name = f"End {index + 1}"
        terminal.data.materials.append(material_terminal)

create_body()
create_coils()
create_terminals()


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
