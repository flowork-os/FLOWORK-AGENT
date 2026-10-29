# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_to_make_a_model_of_basketball" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code to make a model of basketball.

import bpy

# Remove all previous mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the basketball and pattern
basketball_material = bpy.data.materials.new(name='Basketball Color')
basketball_material.diffuse_color = (1, 0.5, 0, 1)
pattern_material = bpy.data.materials.new(name='Stripe Color')
pattern_material.diffuse_color = (0, 0, 0, 1)

# Create a basketball mesh
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
basketball = bpy.context.object
basketball.name = 'Basketball'
basketball.data.materials.append(basketball_material)

# Function to add a stripe
def add_stripe(radius, depth, location, rotation, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
    stripe = bpy.context.object
    stripe.name = name
    stripe.data.materials.append(pattern_material)

# Add stripes
add_stripe(1.01, 0.05, (0, 0, 0), (1.5708, 0, 0), 'Horizontal Stripe')
add_stripe(1.01, 0.05, (0, 0, 0), (0, 1.5708, 0), 'Vertical Stripe')
add_stripe(1.01, 0.05, (0, 0, 0), (0.7854, 0, 0.7854), 'Diagonal Stripe 1')
add_stripe(1.01, 0.05, (0, 0, 0), (-0.7854, 0, 0.7854), 'Diagonal Stripe 2')


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
