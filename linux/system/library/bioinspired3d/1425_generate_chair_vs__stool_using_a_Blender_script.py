# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_chair_vs__stool_using_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate chair vs. stool using a Blender script

import bpy
import math

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a wood material
wood_texture = bpy.data.materials.new(name='Wood Texture')
wood_texture.diffuse_color = (0.55, 0.27, 0.07, 1)

# Function to generate a chair

def generate_chair():
    # Create chair legs
    for idx in range(4):
        leg_x = 0.7 * (idx % 2) - 0.35
        leg_y = 0.7 * (idx // 2) - 0.35
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.9, location=(leg_x, leg_y, -0.45))
        leg = bpy.context.object
        leg.name = f'Chair Leg {idx + 1}'
        leg.data.materials.append(wood_texture)

    # Create chair seat
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, 0, 0))
    seat = bpy.context.object
    seat.name = 'Chair Seat'
    seat.data.materials.append(wood_texture)

    # Create chair backrest
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, -0.5, 0.45))
    backrest = bpy.context.object
    backrest.scale = (0.5, 0.05, 0.45)
    backrest.name = 'Chair Backrest'
    backrest.data.materials.append(wood_texture)

# Function to create a stool

def generate_stool():
    for idx in range(3):
        leg_angle = idx * (2 * math.pi / 3)
        stool_leg_x = 0.35 * math.cos(leg_angle) + 2
        stool_leg_y = 0.35 * math.sin(leg_angle)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.9, location=(stool_leg_x, stool_leg_y, -0.45))
        leg = bpy.context.object
        leg.name = f'Stool Leg {idx + 1}'
        leg.data.materials.append(wood_texture)

    # Create stool seat
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(2, 0, 0))
    stool_seat = bpy.context.object
    stool_seat.name = 'Stool Seat'
    stool_seat.data.materials.append(wood_texture)

# Build the furniture
generate_chair()
generate_stool()


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
