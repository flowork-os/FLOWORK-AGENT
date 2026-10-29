# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_code__construct_floor_lamp" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender code, construct floor lamp

import bpy

# Start fresh by clearing the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Materials for lamp components
base_color_mat = bpy.data.materials.new(name="Base Color")
base_color_mat.diffuse_color = (0.3, 0.3, 0.3, 1)  # Medium gray
shade_color_mat = bpy.data.materials.new(name="Shade Color")
shade_color_mat.diffuse_color = (0.95, 0.95, 0.7, 1)  # Pale yellow

# Create lamp elements
# Base
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.05, location=(0, 0, 0.025))
base_component = bpy.context.object
base_component.name = "Base Component"
base_component.data.materials.append(base_color_mat)

# Stand
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(0, 0, 1.025))
stand_component = bpy.context.object
stand_component.name = "Stand Component"
stand_component.data.materials.append(base_color_mat)

# Lampshade
bpy.ops.mesh.primitive_cone_add(radius1=0.5, radius2=0.2, depth=0.6, location=(0, 0, 2.3))
lampshade_component = bpy.context.object
lampshade_component.name = "Lampshade Component"
lampshade_component.data.materials.append(shade_color_mat)

# Switch
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0.1, 0, 0.5))
switch_component = bpy.context.object
switch_component.name = "Lamp Switch"
switch_component.data.materials.append(base_color_mat)


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
