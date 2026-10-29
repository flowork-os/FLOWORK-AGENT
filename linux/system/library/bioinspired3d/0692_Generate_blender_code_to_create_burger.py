# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_blender_code_to_create_burger" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate blender code to create burger.

import bpy
import random

# Start with a clean scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create and assign a material

def create_material(name, color):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    return mat

# Create materials for burger components
bun_mat = create_material('Bun Material', (0.8, 0.6, 0.4, 1))
cheese_mat = create_material('Cheese Material', (1.0, 0.8, 0.0, 1))
patty_mat = create_material('Patty Material', (0.4, 0.2, 0.1, 1))
tomato_mat = create_material('Tomato Material', (0.8, 0.1, 0.1, 1))
lettuce_mat = create_material('Lettuce Material', (0.2, 0.8, 0.2, 1))

# Function to add a mesh object

def add_mesh_object(primitive_type, name, params, material):
    if primitive_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=params[0], depth=params[1], location=params[2])
    elif primitive_type == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=params[0], location=params[1])
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create burger layers
add_mesh_object('cylinder', 'Bottom Bun', (1.2, 0.3, (0, 0, 0)), bun_mat)
add_mesh_object('cylinder', 'Cheese', (1.25, 0.1, (0, 0, 0.2)), cheese_mat)
add_mesh_object('cylinder', 'Patty', (1.2, 0.3, (0, 0, 0.35)), patty_mat)
add_mesh_object('cylinder', 'Tomato', (1.25, 0.1, (0, 0, 0.55)), tomato_mat)
add_mesh_object('cylinder', 'Lettuce', (1.3, 0.1, (0, 0, 0.65)), lettuce_mat)

# Create the top bun as a sphere
add_mesh_object('sphere', 'Top Bun', (1.2, (0, 0, 1)), bun_mat)

# Create sesame seeds randomly
for _ in range(30):
    x_seed = random.uniform(-1.0, 1.0)
    y_seed = random.uniform(-1.0, 1.0)
    if x_seed**2 + y_seed**2 <= 1.0:
        add_mesh_object('sphere', 'Sesame Seed', (0.05, (x_seed, y_seed, 1.25)), bun_mat)
        seed = bpy.context.object
        seed.scale[2] = 0.2


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
