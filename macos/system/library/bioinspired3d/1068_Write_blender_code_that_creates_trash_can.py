# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_blender_code_that_creates_trash_can" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write blender code that creates trash can.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize a gray material for the model
trash_material = bpy.data.materials.new(name='TrashMaterial')
trash_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Define a class to handle trash can creation
class TrashCan:
    def __init__(self, radius_body, height_body, radius_lid, height_lid):
        self.radius_body = radius_body
        self.height_body = height_body
        self.radius_lid = radius_lid
        self.height_lid = height_lid

    def create_body(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.radius_body, depth=self.height_body, location=(0, 0, self.height_body / 2))
        body = bpy.context.object
        body.name = 'Trash Can Body'
        body.data.materials.append(trash_material)

    def create_lid(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.radius_lid, depth=self.height_lid, location=(0, 0, self.height_body + self.height_lid / 2))
        lid = bpy.context.object
        lid.name = 'Trash Can Lid'
        lid.data.materials.append(trash_material)

# Instantiate and create the trash can
trash_can = TrashCan(1, 2, 1.05, 0.1)
trash_can.create_body()
trash_can.create_lid()


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
