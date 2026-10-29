# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_code_that_creates_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender code that creates transformer.

import bpy

# Clear the current scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the transformer
material_body = bpy.data.materials.new(name='Gray Material')
material_body.diffuse_color = (0.4, 0.4, 0.4, 1)
material_coil = bpy.data.materials.new(name='Bright Red')
material_coil.diffuse_color = (1, 0, 0, 1)
material_terminal = bpy.data.materials.new(name='Dark Shade')
material_terminal.diffuse_color = (0.15, 0.15, 0.15, 1)

# Create the body of the transformer
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
transformer_body = bpy.context.object
transformer_body.name = 'Transformer Base'
transformer_body.scale = (1, 0.5, 1)
transformer_body.data.materials.append(material_body)

# Generate coils and terminals
positions = [(1.2, 0, 0), (-1.2, 0, 0)]
for pos in positions:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.5, location=pos)
    coil = bpy.context.object
    coil.name = 'Coil'
    coil.data.materials.append(material_coil)

for pos in positions:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(pos[0], pos[1], 0.75))
    terminal = bpy.context.object
    terminal.name = 'Terminal'
    terminal.data.materials.append(material_terminal)


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
