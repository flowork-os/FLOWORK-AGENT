# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_blender_code_to_create_a_model_of_wedding_cake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a blender code to create a model of wedding cake.

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material for the model
white_material = bpy.data.materials.new(name='WhiteMaterial')
white_material.diffuse_color = (1, 1, 1, 1)  # Set to white

# Create a class to handle tier creation
class Tier:
    def __init__(self, radius, depth, location, name):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        self.object = bpy.context.object
        self.object.name = name
        self.object.data.materials.append(white_material)

# Instantiate each tier
Tier(1, 0.5, (0, 0, 0.25), 'BaseTier')
Tier(0.75, 0.5, (0, 0, 0.75), 'MiddleTier')
Tier(0.5, 0.5, (0, 0, 1.25), 'TopTier')

# Add rings around each tier
for idx, rad in enumerate([1, 0.75, 0.5]):
    bpy.ops.mesh.primitive_torus_add(major_radius=rad, minor_radius=0.05, location=(0, 0, 0.5 * (idx + 1)))
    ring = bpy.context.object
    ring.name = f'Ring_{idx + 1}'
    ring.data.materials.append(white_material)

# Create a small sphere on top
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 0, 1.55))
topper_object = bpy.context.object
topper_object.name = 'Topper'
topper_object.data.materials.append(white_material)


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
