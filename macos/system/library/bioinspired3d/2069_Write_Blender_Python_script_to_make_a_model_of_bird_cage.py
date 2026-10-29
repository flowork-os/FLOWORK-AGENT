# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Write_Blender_Python_script_to_make_a_model_of_bird_cage" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Write Blender Python script to make a model of bird cage

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

metal_material = bpy.data.materials.new(name="Metallic Surface")
metal_material.diffuse_color = (0.7, 0.7, 0.7, 1)

class CageElement:
    def __init__(self, mesh_type, params, name):
        self.mesh_type = mesh_type
        self.params = params
        self.name = name
        self.create_mesh()

    def create_mesh(self):
        if self.mesh_type == 'cylinder':
            bpy.ops.mesh.primitive_cylinder_add(radius=self.params[0], depth=self.params[1], location=self.params[2])
        elif self.mesh_type == 'sphere':
            bpy.ops.mesh.primitive_uv_sphere_add(radius=self.params[0], location=self.params[1])
        elif self.mesh_type == 'cube':
            bpy.ops.mesh.primitive_cube_add(size=self.params[0], location=self.params[1])
        obj = bpy.context.object
        obj.name = self.name
        obj.data.materials.append(metal_material)

CageElement('cylinder', (1, 0.1, (0, 0, 0)), "Base")
CageElement('sphere', (1, (0, 0, 2)), "Top")
bpy.context.object.scale[2] = 0.5

for i in range(16):
    angle = i * (2 * math.pi / 16)
    x = math.cos(angle)
    y = math.sin(angle)
    CageElement('cylinder', (0.05, 2, (x, y, 1)), f"Bar {i + 1}")

CageElement('cube', (0.5, (1, 0, 1)), "Door")
perch = CageElement('cylinder', (0.05, 1.5, (0, 0, 0.5)), "Perch")
perch.rotation_euler = (0, math.pi/2, 0)

CageElement('torus', (0.2, 0.05, (0, 0, 2.5)), "Hook")


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
