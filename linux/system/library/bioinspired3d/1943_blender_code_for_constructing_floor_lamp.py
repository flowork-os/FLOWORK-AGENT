# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_for_constructing_floor_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code for constructing floor lamp

import bpy

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for lamp components
material_base = bpy.data.materials.new(name="Base Color")
material_base.diffuse_color = (0.15, 0.15, 0.15, 1)  # Darker gray
material_shade = bpy.data.materials.new(name="Shade Color")
material_shade.diffuse_color = (1, 1, 0.9, 1)  # Light yellowish

# Create base of the lamp
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.05, location=(0, 0, 0.025))
base_object = bpy.context.object
base_object.name = "Lamp Base"
base_object.data.materials.append(material_base)

# Create stand of the lamp
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(0, 0, 1.025))
stand_object = bpy.context.object
stand_object.name = "Lamp Stand"
stand_object.data.materials.append(material_base)

# Create lampshade
bpy.ops.mesh.primitive_cone_add(radius1=0.5, radius2=0.2, depth=0.6, location=(0, 0, 2.3))
lampshade_object = bpy.context.object
lampshade_object.name = "Lampshade"
lampshade_object.data.materials.append(material_shade)

# Create switch
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0.1, 0, 0.5))
switch_object = bpy.context.object
switch_object.name = "Switch"
switch_object.data.materials.append(material_base)


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
