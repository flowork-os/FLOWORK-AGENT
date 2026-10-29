# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_blender_code_that_creates_ottoman" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a blender code that creates ottoman.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize ottoman material
ottoman_material = bpy.data.materials.new(name='Material_Ottoman')
ottoman_material.diffuse_color = (0.6, 0.3, 0.15, 1)  # Lighter brown

# Create the ottoman's base
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0.5))
ottoman_base = bpy.context.object
ottoman_base.name = 'Ottoman Base'
ottoman_base.scale[2] = 0.1  # Flattening the base
ottoman_base.data.materials.append(ottoman_material)

# Function to create legs
def create_leg(position, index):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.5, location=position)
    leg = bpy.context.object
    leg.name = f'Leg_{index + 1}'
    leg.data.materials.append(ottoman_material)

# Positions for the legs
leg_positions = [(-0.7, -0.7, 0.25), (0.7, -0.7, 0.25), (-0.7, 0.7, 0.25), (0.7, 0.7, 0.25)]

# Create each leg
for i, pos in enumerate(leg_positions):
    create_leg(pos, i)


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
