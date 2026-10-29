# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_code_create_centrifuge" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender code create centrifuge.

import bpy
import math

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

light_gray = bpy.data.materials.new(name="Light Gray")
light_gray.diffuse_color = (0.5, 0.5, 0.5, 1)
dark_shade = bpy.data.materials.new(name="Dark Shade")
dark_shade.diffuse_color = (0.2, 0.2, 0.2, 1)
navy_blue = bpy.data.materials.new(name="Navy Blue")
navy_blue.diffuse_color = (0.0, 0.0, 1.0, 1)

def add_holder(index):
    angle = index * (math.pi / 2)
    x = 0.7 * math.cos(angle)
    y = 0.7 * math.sin(angle)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.4, location=(x, y, 2.1), rotation=(math.pi / 2, 0, angle))
    holder = bpy.context.object
    holder.name = f"Sample Holder {index + 1}"
    holder.data.materials.append(dark_shade)

bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
main_body = bpy.context.object
main_body.name = "Main Body"
main_body.data.materials.append(light_gray)

bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.2, location=(0, 0, 2))
rotor = bpy.context.object
rotor.name = "Rotor"
rotor.data.materials.append(dark_shade)

for i in range(4):
    add_holder(i)

bpy.ops.mesh.primitive_cube_add(size=0.5, location=(1.1, 0, 1.5))
control_panel = bpy.context.object
control_panel.name = "Control Panel"
control_panel.data.materials.append(navy_blue)


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
