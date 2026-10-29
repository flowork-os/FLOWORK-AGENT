# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_python_code__build_a_model_of_basketball" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender python code, build a model of basketball.

import bpy

# Clear all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the basketball
basketball_color = bpy.data.materials.new(name='Basketball Color')
basketball_color.diffuse_color = (1, 0.55, 0, 1)  # Bright orange
pattern_color = bpy.data.materials.new(name='Pattern Color')
pattern_color.diffuse_color = (0, 0, 0, 1)  # Classic black

# Function to create a cylinder stripe
def create_stripe(radius, depth, location, rotation, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
    stripe = bpy.context.object
    stripe.name = name
    stripe.data.materials.append(material)
    return stripe

# Create the basketball
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
basketball = bpy.context.object
basketball.name = 'Basketball'
basketball.data.materials.append(basketball_color)

# Add patterns using the helper function
create_stripe(1.01, 0.05, (0, 0, 0), (1.5708, 0, 0), 'Horizontal Stripe', pattern_color)
create_stripe(1.01, 0.05, (0, 0, 0), (0, 1.5708, 0), 'Vertical Stripe', pattern_color)
create_stripe(1.01, 0.05, (0, 0, 0), (0.7854, 0, 0.7854), 'Diagonal Stripe 1', pattern_color)
create_stripe(1.01, 0.05, (0, 0, 0), (-0.7854, 0, 0.7854), 'Diagonal Stripe 2', pattern_color)


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
