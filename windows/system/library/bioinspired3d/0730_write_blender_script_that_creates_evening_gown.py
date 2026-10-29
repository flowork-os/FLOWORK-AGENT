# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_script_that_creates_evening_gown" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender script that creates evening gown

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create gown material
gown_material = bpy.data.materials.new(name='Gown Material')
gown_material.diffuse_color = (0.1, 0.1, 0.3, 1)  # Dark blue color

# Function to build the dress
class Dress:
    def __init__(self):
        self.create_bodice()
        self.create_skirt()
        self.create_sleeves(2)
        self.create_neckline()
        self.create_zipper()

    def create_bodice(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.2, location=(0, 0, 1.1))
        bodice = bpy.context.object
        bodice.name = 'Bodice'
        bodice.scale = (1, 1, 1.5)
        bodice.data.materials.append(gown_material)

    def create_skirt(self):
        bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0, depth=2, location=(0, 0, 0))
        skirt = bpy.context.object
        skirt.name = 'Skirt'
        skirt.data.materials.append(gown_material)

    def create_sleeves(self, count):
        for i in range(count):
            x_pos = 0.35 * (i * 2 - 1)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=1.2, location=(x_pos, 0, 1.1))
            sleeve = bpy.context.object
            sleeve.name = f'Sleeve {i + 1}'
            sleeve.rotation_euler[1] = 1.57  # Horizontal rotation
            sleeve.data.materials.append(gown_material)

    def create_neckline(self):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.35, minor_radius=0.05, location=(0, 0, 1.7))
        neckline = bpy.context.object
        neckline.name = 'Neckline'
        neckline.scale = (1, 1, 0.3)
        neckline.data.materials.append(gown_material)

    def create_zipper(self):
        bpy.ops.mesh.primitive_cube_add(size=0.02, location=(0, -0.3, 0.5))
        zipper = bpy.context.object
        zipper.name = 'Zipper'
        zipper.scale = (1, 1, 10)
        zipper.data.materials.append(gown_material)

# Instantiate the dress
Dress()


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
