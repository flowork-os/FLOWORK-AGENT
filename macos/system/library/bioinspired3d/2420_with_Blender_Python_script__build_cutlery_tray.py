# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_Blender_Python_script__build_cutlery_tray" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with Blender Python script, build cutlery tray

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the tray
material_gray = bpy.data.materials.new(name='GrayMaterial')
material_gray.diffuse_color = (0.8, 0.8, 0.8, 1)

# Class to handle tray creation
class Tray:
    def __init__(self):
        self.base = self.create_base()
        self.create_dividers()

    def create_base(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        base_object = bpy.context.object
        base_object.name = 'TrayBase'
        base_object.scale[2] = 0.1
        base_object.data.materials.append(material_gray)
        return base_object

    def create_dividers(self):
        # Create horizontal dividers
        for i in range(1, 3):
            self.add_divider((0, i * 0.5 - 0.5, 0.1), f'HorizontalDivider_{i}', (1, 0.05, 0.2))

        # Create vertical dividers
        for i in range(1, 4):
            self.add_divider((i * 0.5 - 1, 0, 0.1), f'VerticalDivider_{i}', (0.05, 1, 0.2))

    def add_divider(self, location, name, scale):
        bpy.ops.mesh.primitive_cube_add(size=1, location=location)
        divider_object = bpy.context.object
        divider_object.name = name
        divider_object.scale = scale
        divider_object.data.materials.append(material_gray)

# Create the tray
tray = Tray()


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
