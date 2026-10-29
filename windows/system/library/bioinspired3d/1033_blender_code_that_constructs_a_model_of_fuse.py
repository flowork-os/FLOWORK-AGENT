# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_code_that_constructs_a_model_of_fuse" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender code that constructs a model of fuse.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
material_glass = bpy.data.materials.new(name='Glass Material')
material_glass.diffuse_color = (0.8, 0.8, 0.8, 1)
material_metal = bpy.data.materials.new(name='Metal Material')
material_metal.diffuse_color = (0.5, 0.5, 0.5, 1)

# Create the main glass cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.0, location=(0, 0, 0))
main_body = bpy.context.object
main_body.name = 'Glass Cylinder'
main_body.data.materials.append(material_glass)

# Create caps using a loop
for z_position in [-0.6, 0.6]:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.2, location=(0, 0, z_position))
    cap = bpy.context.object
    cap.name = f'Metal Cap at {z_position}'
    cap.data.materials.append(material_metal)


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
