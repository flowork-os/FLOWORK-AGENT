# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_hammer_vs__mallet_in_a_Blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct hammer vs. mallet in a Blender script

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

steel_material = bpy.data.materials.new(name='Steel')
steel_material.diffuse_color = (0.8, 0.8, 0.8, 1)
cherry_wood_material = bpy.data.materials.new(name='CherryWood')
cherry_wood_material.diffuse_color = (0.7, 0.4, 0.2, 1)

class Tool:
    def __init__(self, radius, depth, location, name, material):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
        self.obj = bpy.context.object
        self.obj.name = name
        self.obj.data.materials.append(material)

hammer_handle = Tool(0.05, 1, (-1, 0, 0), 'Hammer_Handle', cherry_wood_material)

bpy.ops.mesh.primitive_cube_add(size=0.3, location=(-1, 0, 0.5))
hammer_head = bpy.context.object
hammer_head.name = 'Hammer_Head'
hammer_head.data.materials.append(steel_material)

mallet_handle = Tool(0.05, 1, (1, 0, 0), 'Mallet_Handle', cherry_wood_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.4, location=(1, 0, 0.5))
mallet_head = bpy.context.object
mallet_head.name = 'Mallet_Head'
mallet_head.data.materials.append(steel_material)
mallet_head.rotation_euler = (1.5708, 0, 0)


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
