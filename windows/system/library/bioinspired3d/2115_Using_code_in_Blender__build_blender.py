# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_code_in_Blender__build_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using code in Blender, build blender

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

base_material = create_material('Base Material', (0.2, 0.2, 0.2, 1))
button_material = create_material('Button Material', (0.8, 0.1, 0.1, 1))
dial_material = create_material('Dial Material', (0.1, 0.1, 0.8, 1))
jar_material = create_material('Jar Material', (0.8, 0.8, 0.9, 0.3))
lid_material = create_material('Lid Material', (0.2, 0.2, 0.2, 1))

bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
base_obj = bpy.context.object
base_obj.name = 'Base'
base_obj.data.materials.append(base_material)

for index in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0.3 * (index - 1), 0.9, 0.5))
    button_obj = bpy.context.object
    button_obj.name = f'Button {index + 1}'
    button_obj.data.materials.append(button_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.05, location=(0, 0.9, 0.55))
dial_obj = bpy.context.object
dial_obj.name = 'Dial'
dial_obj.data.materials.append(dial_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=2, location=(0, 0, 1.5))
jar_obj = bpy.context.object
jar_obj.name = 'Jar'
jar_obj.data.materials.append(jar_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=0.1, location=(0, 0, 2.55))
lid_obj = bpy.context.object
lid_obj.name = 'Lid'
lid_obj.data.materials.append(lid_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.1, location=(0, 0, 2.6))
center_cap_obj = bpy.context.object
center_cap_obj.name = 'Center Cap'
center_cap_obj.data.materials.append(lid_material)


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
