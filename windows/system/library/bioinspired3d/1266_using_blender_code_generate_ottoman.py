# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_code_generate_ottoman" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender code generate ottoman.

import bpy

# Remove existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Set up the ottoman material
ottoman_material = bpy.data.materials.new(name="Ottoman Color")
ottoman_material.diffuse_color = (0.4, 0.2, 0.1, 1)  # Darker shade of brown

# Define a class for the Ottoman
class Ottoman:
    def __init__(self):
        self.base = self.create_base()
        self.legs = self.create_legs()

    def create_base(self):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.25))
        base = bpy.context.object
        base.name = "Ottoman Base"
        base.scale = (1, 1, 0.3)
        base.data.materials.append(ottoman_material)
        return base

    def create_legs(self):
        for i in range(4):
            x = 0.4 * (i % 2 * 2 - 1)
            y = 0.4 * (i // 2 * 2 - 1)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.3, location=(x, y, 0.15))
            leg = bpy.context.object
            leg.name = f"Leg {i + 1}"
            leg.data.materials.append(ottoman_material)

# Instantiate the Ottoman class
ottoman = Ottoman()


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
