# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_a_Blender_script_generate_burger" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using a Blender script generate burger.

import bpy
import random

# Remove all mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material colors for the burger layers
bun_color = (0.8, 0.6, 0.4, 1)
lettuce_color = (0.2, 0.8, 0.2, 1)
tomato_color = (0.8, 0.1, 0.1, 1)
patty_color = (0.4, 0.2, 0.1, 1)
cheese_color = (1.0, 0.8, 0.0, 1)

# Function to add a cylinder

def add_cylinder(name, radius, depth, position, color):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    mesh_object = bpy.context.object
    mesh_object.name = name
    mat = bpy.data.materials.new(name=name + ' Material')
    mat.diffuse_color = color
    mesh_object.data.materials.append(mat)

# Create burger components
add_cylinder('Bottom Bun', 1.2, 0.3, (0, 0, 0), bun_color)
add_cylinder('Cheese', 1.25, 0.1, (0, 0, 0.2), cheese_color)
add_cylinder('Patty', 1.2, 0.3, (0, 0, 0.35), patty_color)
add_cylinder('Tomato', 1.25, 0.1, (0, 0, 0.55), tomato_color)
add_cylinder('Lettuce', 1.3, 0.1, (0, 0, 0.65), lettuce_color)

# Create the top bun as a sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, location=(0, 0, 1))
top_bun = bpy.context.object
bpy.context.object.scale[2] = 0.5
bpy.context.object.name = 'Top Bun'
material = bpy.data.materials.new(name='Top Bun Material')
material.diffuse_color = bun_color
bpy.context.object.data.materials.append(material)

# Generate sesame seeds
for _ in range(30):
    sx = random.uniform(-1.0, 1.0)
    sy = random.uniform(-1.0, 1.0)
    if sx**2 + sy**2 <= 1.0:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(sx, sy, 1.25))
        seed = bpy.context.object
        seed.scale[2] = 0.2
        seed.data.materials.append(material)


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
