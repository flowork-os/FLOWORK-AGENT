# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_blender_code_to_create_a_model_of_screwdriver" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write blender code to create a model of screwdriver.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials
handle_color = bpy.data.materials.new(name='Grip Color')
handle_color.diffuse_color = (0.7, 0.1, 0.1, 1)  # Dark red
metal_color = bpy.data.materials.new(name='Shaft Color')
metal_color.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light gray

# Create handle
bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.0, location=(0, 0, 0.5))
handle = bpy.context.object
handle.name = 'Handle'
handle.data.materials.append(handle_color)

# Create shaft
bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=1.5, location=(0, 0, -0.75))
shaft = bpy.context.object
shaft.name = 'Shaft'
shaft.data.materials.append(metal_color)

# Create flat tip
bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0, 0, -1.55))
tip = bpy.context.object
tip.scale[1] = 0.03  # Adjust the flatness
tip.name = 'Flat Tip'
tip.data.materials.append(metal_color)


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
