# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_blender_code__build_a_model_of_birthday_cake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with blender code, build a model of birthday cake

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the cake and icing
cake_texture = bpy.data.materials.new(name="Cake Texture")
cake_texture.diffuse_color = (0.8, 0.6, 0.4, 1)
icings_texture = bpy.data.materials.new(name="Icing Texture")
icings_texture.diffuse_color = (1, 0.8, 0.8, 1)

# Generate the cake layers
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.3, location=(0, 0, 0))
bottom = bpy.context.object
bottom.name = "Base Layer"
bottom.data.materials.append(cake_texture)

bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=0.3, location=(0, 0, 0.3))
middle = bpy.context.object
middle.name = "Middle Layer"
middle.data.materials.append(cake_texture)

bpy.ops.mesh.primitive_cylinder_add(radius=0.6, depth=0.3, location=(0, 0, 0.6))
top = bpy.context.object
top.name = "Top Layer"
top.data.materials.append(cake_texture)

# Create icing layer
bpy.ops.mesh.primitive_cylinder_add(radius=0.65, depth=0.1, location=(0, 0, 0.75))
icings = bpy.context.object
icings.name = "Icing"
icings.data.materials.append(icings_texture)


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
