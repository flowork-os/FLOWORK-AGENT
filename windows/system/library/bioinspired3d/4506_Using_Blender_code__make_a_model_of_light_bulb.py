# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Using_Blender_code__make_a_model_of_light_bulb" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Using Blender code, make a model of light bulb

import bpy

# Clear the current scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Establish materials
clear_glass = bpy.data.materials.new(name='Clear Glass')
clear_glass.diffuse_color = (1, 1, 1, 0.1)  # Clear glass color
base_metal = bpy.data.materials.new(name='Base Metal')
base_metal.diffuse_color = (0.5, 0.5, 0.5, 1)  # Metal color

# Create glass top
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1.5))
glass_entity = bpy.context.object
glass_entity.name = 'Glass Top'
glass_entity.data.materials.append(clear_glass)

# Create screw base
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1, location=(0, 0, 0.5))
screw_entity = bpy.context.object
screw_entity.name = 'Screw Base'
screw_entity.data.materials.append(base_metal)

# Create filament
bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.02, location=(0, 0, 1.5))
filament_entity = bpy.context.object
filament_entity.name = 'Filament'
filament_entity.data.materials.append(base_metal)


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
