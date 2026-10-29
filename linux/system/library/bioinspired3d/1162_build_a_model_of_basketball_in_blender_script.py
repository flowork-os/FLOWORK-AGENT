# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, build_a_model_of_basketball_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: build a model of basketball in blender script

import bpy

# Clear the current mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials
mat_orange = bpy.data.materials.new(name='Orange Material')
mat_orange.diffuse_color = (1, 0.6, 0.2, 1)  # Adjusted to a lighter orange
mat_black = bpy.data.materials.new(name='Black Material')
mat_black.diffuse_color = (0, 0, 0, 1)  # Standard black

# Create a basketball object
basketball_obj = bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
basketball = bpy.context.object
basketball.name = 'Basketball'
basketball.data.materials.append(mat_orange)

# Create stripes using direct calls
bpy.ops.mesh.primitive_cylinder_add(radius=1.01, depth=0.05, location=(0, 0, 0), rotation=(1.5708, 0, 0))
stripe1 = bpy.context.object
stripe1.name = 'Horizontal Stripe'
stripe1.data.materials.append(mat_black)

bpy.ops.mesh.primitive_cylinder_add(radius=1.01, depth=0.05, location=(0, 0, 0), rotation=(0, 1.5708, 0))
stripe2 = bpy.context.object
stripe2.name = 'Vertical Stripe'
stripe2.data.materials.append(mat_black)

bpy.ops.mesh.primitive_cylinder_add(radius=1.01, depth=0.05, location=(0, 0, 0), rotation=(0.7854, 0, 0.7854))
stripe3 = bpy.context.object
stripe3.name = 'Diagonal Stripe 1'
stripe3.data.materials.append(mat_black)

bpy.ops.mesh.primitive_cylinder_add(radius=1.01, depth=0.05, location=(0, 0, 0), rotation=(-0.7854, 0, 0.7854))
stripe4 = bpy.context.object
stripe4.name = 'Diagonal Stripe 2'
stripe4.data.materials.append(mat_black)


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
