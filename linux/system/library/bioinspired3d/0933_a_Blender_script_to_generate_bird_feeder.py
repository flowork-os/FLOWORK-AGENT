# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_to_generate_bird_feeder" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script to generate bird feeder.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the feeder and roof
feeder_mat = bpy.data.materials.new(name='Feeder Material')
feeder_mat.diffuse_color = (0.5, 0.3, 0.1, 1)

roof_mat = bpy.data.materials.new(name='Roof Material')
roof_mat.diffuse_color = (0.2, 0.2, 0.2, 1)

# Define a class for the feeder structure
class Feeder:
    def __init__(self):
        self.feeder_body = self.create_body()
        self.roof = self.create_roof()
        self.seed_tray = self.create_seed_tray()
        self.perch = self.create_perch()

    def create_body(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1, location=(0, 0, 0.5))
        body = bpy.context.object
        body.name = 'Feeder Body'
        body.data.materials.append(feeder_mat)
        return body

    def create_roof(self):
        bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0.2, depth=0.5, location=(0, 0, 1.25))
        roof = bpy.context.object
        roof.name = 'Roof'
        roof.data.materials.append(roof_mat)
        return roof

    def create_seed_tray(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.55, depth=0.1, location=(0, 0, 0.05))
        tray = bpy.context.object
        tray.name = 'Seed Tray'
        tray.data.materials.append(feeder_mat)
        return tray

    def create_perch(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.6, location=(0, 0.55, 0.1), rotation=(0, 1.57, 0))
        perch = bpy.context.object
        perch.name = 'Perch'
        perch.data.materials.append(feeder_mat)
        return perch

# Instantiate the feeder
Feeder()


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
