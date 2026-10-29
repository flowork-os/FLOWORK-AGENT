# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_python_code_make_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender python code make transformer.

import bpy

# Remove all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for different components
mat_body = bpy.data.materials.new(name='Main Body Color')
mat_body.diffuse_color = (0.7, 0.7, 0.7, 1)
mat_coil = bpy.data.materials.new(name='Coil Color')
mat_coil.diffuse_color = (0.9, 0.0, 0.0, 1)
mat_terminal = bpy.data.materials.new(name='Terminal Color')
mat_terminal.diffuse_color = (0.3, 0.3, 0.3, 1)

# Create a rectangular body
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
transformer = bpy.context.object
transformer.name = 'Rectangular Body'
transformer.scale = (1, 0.5, 1)
transformer.data.materials.append(mat_body)

# Function to create coils and terminals
def create_parts():
    for i in range(2):
        x_pos = 1.2 * (i * 2 - 1)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.5, location=(x_pos, 0, 0))
        coil = bpy.context.object
        coil.name = f'Coil {i + 1}'
        coil.data.materials.append(mat_coil)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(x_pos, 0, 0.75))
        terminal = bpy.context.object
        terminal.name = f'Terminal {i + 1}'
        terminal.data.materials.append(mat_terminal)

create_parts()


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
