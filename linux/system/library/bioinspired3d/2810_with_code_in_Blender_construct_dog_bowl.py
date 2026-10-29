# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_code_in_Blender_construct_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with code in Blender construct dog bowl.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

bowl_mat = bpy.data.materials.new(name='BowlMaterial')
bowl_mat.diffuse_color = (0.8, 0.3, 0.1, 1)
kibble_mat = bpy.data.materials.new(name='KibbleMaterial')
kibble_mat.diffuse_color = (0.6, 0.4, 0.2, 1)

class Bowl:
    def __init__(self, radius, depth, position):
        self.bowl = self.create_bowl(radius, depth, position)

    def create_bowl(self, radius, depth, position):
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
        obj = bpy.context.object
        obj.data.materials.append(bowl_mat)
        return obj

bowl_instance = Bowl(1, 0.5, (0, 0, 0))
dip_instance = Bowl(0.8, 0.4, (0, 0, 0.05))

bool_mod = bowl_instance.bowl.modifiers.new(type='BOOLEAN', name='DipModifier')
bool_mod.operation = 'DIFFERENCE'
bool_mod.object = dip_instance.bowl
bpy.context.view_layer.objects.active = bowl_instance.bowl
bpy.ops.object.modifier_apply(modifier='DipModifier')
bpy.data.objects.remove(dip_instance.bowl)

for i in range(5):
    x_pos = 0.5 * (i % 2) - 0.25
    y_pos = 0.5 * (i // 2) - 0.25
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(x_pos, y_pos, 0.1))
    kibble_piece = bpy.context.object
    kibble_piece.name = f'Kibble_{i + 1}'
    kibble_piece.data.materials.append(kibble_mat)


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
