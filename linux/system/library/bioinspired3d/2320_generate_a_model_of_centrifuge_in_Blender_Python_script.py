# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_centrifuge_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of centrifuge in Blender Python script

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

material_light_gray = bpy.data.materials.new(name="Material Light Gray")
material_light_gray.diffuse_color = (0.5, 0.5, 0.5, 1)
material_dark_gray = bpy.data.materials.new(name="Material Dark Gray")
material_dark_gray.diffuse_color = (0.2, 0.2, 0.2, 1)
material_blue_color = bpy.data.materials.new(name="Material Blue")
material_blue_color.diffuse_color = (0.0, 0.0, 1.0, 1)

class Centrifuge:
    def __init__(self):
        self.create_body()
        self.create_rotor()
        self.create_sample_holders()
        self.create_control_panel()

    def create_body(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
        body = bpy.context.object
        body.name = "Centrifuge Body"
        body.data.materials.append(material_light_gray)

    def create_rotor(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.2, location=(0, 0, 2))
        rotor = bpy.context.object
        rotor.name = "Rotor"
        rotor.data.materials.append(material_dark_gray)

    def create_sample_holders(self):
        for i in range(4):
            angle = i * (math.pi / 2)
            x = 0.7 * math.cos(angle)
            y = 0.7 * math.sin(angle)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(x, y, 2.1), rotation=(math.pi / 2, 0, angle))
            holder = bpy.context.object
            holder.name = f"Sample Holder {i + 1}"
            holder.data.materials.append(material_dark_gray)

    def create_control_panel(self):
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1.1, 0, 1.5))
        panel = bpy.context.object
        panel.name = "Control Panel"
        panel.data.materials.append(material_blue_color)

Centrifuge()


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
