# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_code_in_Blender_create_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With code in Blender create sofa

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the sofa and cushions
brown_material = bpy.data.materials.new(name='Brown Sofa')
brown_material.diffuse_color = (0.5, 0.3, 0.2, 1)
beige_material = bpy.data.materials.new(name='Beige Cushion')
beige_material.diffuse_color = (0.8, 0.7, 0.6, 1)

# Create a sofa object class
class Sofa:
    def __init__(self):
        self.parts = []

    def add_part(self, size, location, scale, name, material):
        bpy.ops.mesh.primitive_cube_add(size=size, location=location)
        part = bpy.context.object
        part.scale = scale
        part.name = name
        part.data.materials.append(material)
        self.parts.append(part)

sofa = Sofa()

# Build the sofa base
sofa.add_part(2, (0, 0, 0.5), (3, 1, 0.5), 'Sofa Base', brown_material)

# Add the backrest
sofa.add_part(2, (0, -1, 1.25), (3, 0.2, 0.75), 'Backrest', brown_material)

# Add armrests
for i in range(2):
    x_position = 3 * (i * 2 - 1)
    sofa.add_part(2, (x_position, 0, 0.75), (0.2, 1, 0.75), f'Armrest {i + 1}', brown_material)

# Add cushions
for i in range(3):
    x_cushion = (i - 1) * 2
    sofa.add_part(2, (x_cushion, 0, 1.1), (0.9, 0.9, 0.2), f'Cushion Seat {i + 1}', beige_material)
    sofa.add_part(2, (x_cushion, -0.9, 1.7), (0.9, 0.2, 0.5), f'Cushion Back {i + 1}', beige_material)

# Create legs
for i in range(4):
    leg_x = 2.8 * (i % 2) - 1.4
    leg_y = 0.8 * (i // 2) - 0.4
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(leg_x, leg_y, 0.2))
    leg = bpy.context.object
    leg.name = f'Leg {i + 1}'
    leg.data.materials.append(brown_material)


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
