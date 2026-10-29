# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_script__make_a_model_of_skateboard" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender script, make a model of skateboard.

import bpy

# Step 1: Clear the Scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the model
material_deck = bpy.data.materials.new(name='Deck Material')
material_deck.diffuse_color = (0.3, 0.3, 0.3, 1)  # Medium gray
material_wheel = bpy.data.materials.new(name='Wheel Material')
material_wheel.diffuse_color = (0.05, 0.05, 0.05, 1)  # Almost black

# Step 2: Create the Deck
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.1))
deck_object = bpy.context.object
deck_object.scale = (3, 0.5, 0.1)
deck_object.name = 'Deck'
deck_object.data.materials.append(material_deck)

# Step 3: Create the Wheels
wheel_locations = [(-2.5, 0.6, -0.1), (-2.5, -0.6, -0.1), (2.5, 0.6, -0.1), (2.5, -0.6, -0.1)]
for index, location in enumerate(wheel_locations):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.1, location=location, rotation=(1.5708, 0, 0))
    wheel_object = bpy.context.object
    wheel_object.name = f'Wheel_{index + 1}'
    wheel_object.data.materials.append(material_wheel)


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
