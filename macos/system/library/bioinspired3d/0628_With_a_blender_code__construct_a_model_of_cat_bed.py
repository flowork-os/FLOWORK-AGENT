# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_a_blender_code__construct_a_model_of_cat_bed" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With a blender code, construct a model of cat bed

import bpy

# Clean the scene by deleting all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the cat bed
light_gray = bpy.data.materials.new(name='Light Gray')
light_gray.diffuse_color = (0.8, 0.8, 0.8, 1)
dark_brown = bpy.data.materials.new(name='Dark Brown')
dark_brown.diffuse_color = (0.4, 0.2, 0.1, 1)

# Add base cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.2, location=(0, 0, 0))
base_obj = bpy.context.object
base_obj.name = 'Base'
base_obj.data.materials.append(light_gray)

# Add torus for sides
bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.2, location=(0, 0, 0.2))
sides_obj = bpy.context.object
sides_obj.name = 'Sides'
sides_obj.data.materials.append(dark_brown)

# Add soft interior cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.9, depth=0.15, location=(0, 0, 0.025))
interior_obj = bpy.context.object
interior_obj.name = 'Soft Interior'
interior_obj.data.materials.append(light_gray)


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
