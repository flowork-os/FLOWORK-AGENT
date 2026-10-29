# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_python_blender_code_that_creates_a_model_of_skateboard" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write python blender code that creates a model of skateboard.

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a material

def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

# Create materials
deck_mat = create_material('Deck Material', (0.25, 0.25, 0.25, 1))  # Gray
wheel_mat = create_material('Wheel Material', (0.1, 0.1, 0.1, 1))  # Very dark gray

# Create Deck
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.1))
deck_mesh = bpy.context.object

deck_mesh.scale = (3, 0.5, 0.1)
deck_mesh.name = 'Deck'
deck_mesh.data.materials.append(deck_mat)

# Create Wheels
wheel_coords = [(-2.5, 0.6, -0.1), (-2.5, -0.6, -0.1), (2.5, 0.6, -0.1), (2.5, -0.6, -0.1)]
for idx, coord in enumerate(wheel_coords):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.1, location=coord, rotation=(1.5708, 0, 0))
    wheel_cylinder = bpy.context.object
    wheel_cylinder.name = f'Wheel_{idx + 1}'
    wheel_cylinder.data.materials.append(wheel_mat)


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
