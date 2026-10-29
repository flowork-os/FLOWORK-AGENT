# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_a_Blender_script_create_a_model_of_skateboard" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using a Blender script create a model of skateboard

import bpy

# Clear the mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials
mat_deck = bpy.data.materials.new('Deck')
mat_deck.diffuse_color = (0.4, 0.4, 0.4, 1)  # Light gray
mat_wheel = bpy.data.materials.new('Wheel')
mat_wheel.diffuse_color = (0.15, 0.15, 0.15, 1)  # Darker gray

# Add Deck
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.1))
deck = bpy.context.object

deck.scale = (3, 0.5, 0.1)
deck.name = 'Deck'
deck.data.materials.append(mat_deck)

# Add Wheels
wheel_positions = [(-2.5, 0.6, -0.1), (-2.5, -0.6, -0.1), (2.5, 0.6, -0.1), (2.5, -0.6, -0.1)]
for i in range(4):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.1, location=wheel_positions[i], rotation=(1.5708, 0, 0))
    wheel = bpy.context.object
    wheel.name = f'Wheel {i + 1}'
    wheel.data.materials.append(mat_wheel)


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
