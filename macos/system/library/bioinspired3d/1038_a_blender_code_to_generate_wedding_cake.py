# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_blender_code_to_generate_wedding_cake" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a blender code to generate wedding cake

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a white material
material_white = bpy.data.materials.new(name='Material_White')
material_white.diffuse_color = (1, 1, 1, 1)  # RGB White

# Function to create a cylinder tier

def create_cylinder(radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    tier = bpy.context.object
    tier.name = name
    tier.data.materials.append(material_white)
    return tier

# Create tiers using the helper function
create_cylinder(1, 0.5, (0, 0, 0.25), 'Bottom_Tier')
create_cylinder(0.75, 0.5, (0, 0, 0.75), 'Middle_Tier')
create_cylinder(0.5, 0.5, (0, 0, 1.25), 'Top_Tier')

# Create rings around each tier
for index, radius in enumerate([1, 0.75, 0.5]):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.05, location=(0, 0, 0.5 * (index + 1)))
    ring_object = bpy.context.object
    ring_object.name = f'Pattern_Ring_{index + 1}'
    ring_object.data.materials.append(material_white)

# Add the final decorative sphere on top
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 0, 1.55))
topper_sphere = bpy.context.object
topper_sphere.name = 'Topper'
topper_sphere.data.materials.append(material_white)


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
