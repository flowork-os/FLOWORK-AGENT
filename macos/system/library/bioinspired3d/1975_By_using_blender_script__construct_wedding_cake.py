# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_script__construct_wedding_cake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender script, construct wedding cake

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a white material
mat_white = bpy.data.materials.new(name='WhiteMaterial')
mat_white.diffuse_color = (1, 1, 1, 1)  # White

# Function to add tiers to the scene
def add_tier(radius, height, position):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    bpy.context.object.data.materials.append(mat_white)

# Add the tiers to the scene
add_tier(1, 0.5, (0, 0, 0.25))
add_tier(0.75, 0.5, (0, 0, 0.75))
add_tier(0.5, 0.5, (0, 0, 1.25))

# Create rings around the tiers
ring_radius = [1, 0.75, 0.5]
for i in range(len(ring_radius)):
    bpy.ops.mesh.primitive_torus_add(major_radius=ring_radius[i], minor_radius=0.05, location=(0, 0, 0.5 * (i + 1)))
    ring = bpy.context.object
    ring.name = f'OuterRing_{i + 1}'
    ring.data.materials.append(mat_white)

# Add a small decorative sphere on top
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 0, 1.55))
topper = bpy.context.object
topper.name = 'Topper'
topper.data.materials.append(mat_white)


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
