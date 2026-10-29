# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_code_that_builds_dog_bowl" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender code that builds dog bowl.

import bpy

def clear_scene():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

clear_scene()

class Bowl:
    def __init__(self, outer_radius, inner_radius, outer_depth, inner_depth, position):
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.outer_depth = outer_depth
        self.inner_depth = inner_depth
        self.position = position
        self.create_bowl()

    def create_bowl(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=self.outer_radius, depth=self.outer_depth, location=self.position)
        outer = bpy.context.object
        outer.name = 'BowlOuter'

        bpy.ops.mesh.primitive_cylinder_add(radius=self.inner_radius, depth=self.inner_depth, location=(self.position[0], self.position[1], self.position[2] + 0.05))
        inner = bpy.context.object
        inner.name = 'BowlInner'

        bool_modifier = outer.modifiers.new(type='BOOLEAN', name='BowlBoolean')
        bool_modifier.operation = 'DIFFERENCE'
        bool_modifier.object = inner
        bpy.context.view_layer.objects.active = outer
        bpy.ops.object.modifier_apply(modifier='BowlBoolean')

        bpy.data.objects.remove(inner, do_unlink=True)

        self.add_material(outer)

    def add_material(self, obj):
        material = bpy.data.materials.new(name='BowlMaterial')
        material.diffuse_color = (0.2, 0.2, 0.8, 1)  # Blue color
        obj.data.materials.append(material)

bowl_instance = Bowl(1.5, 1.3, 0.5, 0.4, (0, 0, 0))


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
