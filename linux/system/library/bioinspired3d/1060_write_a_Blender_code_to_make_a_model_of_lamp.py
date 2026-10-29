# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_a_Blender_code_to_make_a_model_of_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write a Blender code to make a model of lamp.

import bpy

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the lamp components
lamp_material = bpy.data.materials.new(name='LampMaterial')
lamp_material.diffuse_color = (0.8, 0.8, 0.8, 1)

decor_material = bpy.data.materials.new(name='DecorMaterial')
decor_material.diffuse_color = (0.5, 0.2, 0.2, 1)

# Lamp component creation
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.1, location=(0, 0, 0))
base_part = bpy.context.object
base_part.name = 'Lamp Base'
base_part.data.materials.append(lamp_material)

bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1, location=(0, 0, 0.55))
stand_part = bpy.context.object
stand_part.name = 'Lamp Stand'
stand_part.data.materials.append(lamp_material)

bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0.2, depth=0.8, location=(0, 0, 1.3))
shade_part = bpy.context.object
shade_part.name = 'Lamp Shade'
shade_part.data.materials.append(lamp_material)

bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.05, location=(0, 0, 0.05))
decor_part = bpy.context.object
decor_part.name = 'Decorative Ring'
decor_part.data.materials.append(decor_material)


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
