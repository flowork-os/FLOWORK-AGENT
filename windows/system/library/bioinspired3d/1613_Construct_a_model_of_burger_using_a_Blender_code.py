# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Construct_a_model_of_burger_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Construct a model of burger using a Blender code

import bpy
import random

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions for the components of the burger
colors = {
    'bun': (0.8, 0.6, 0.4, 1),  # Light brown for the bun
    'lettuce': (0.2, 0.8, 0.2, 1),  # Green for the lettuce
    'tomato': (0.8, 0.1, 0.1, 1),  # Red for the tomato
    'patty': (0.4, 0.2, 0.1, 1),  # Brown for the beef patty
    'cheese': (1.0, 0.8, 0.0, 1)  # Yellow for the cheese
}

# Function to create a cylinder
def create_cylinder(name, radius, depth, location, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Function to create the top bun with a sphere
def create_top_bun(name, radius, location, scale_z, material):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    top_bun = bpy.context.object
    top_bun.scale[2] = scale_z
    top_bun.name = name
    top_bun.data.materials.append(material)
    return top_bun

# Create materials and assign them
bun_material = bpy.data.materials.new(name='Bun Material')
bun_material.diffuse_color = colors['bun']
cheese_material = bpy.data.materials.new(name='Cheese Material')
cheese_material.diffuse_color = colors['cheese']
patty_material = bpy.data.materials.new(name='Patty Material')
patty_material.diffuse_color = colors['patty']
tomato_material = bpy.data.materials.new(name='Tomato Material')
tomato_material.diffuse_color = colors['tomato']
lettuce_material = bpy.data.materials.new(name='Lettuce Material')
lettuce_material.diffuse_color = colors['lettuce']

# Create the burger components
bottom_bun = create_cylinder('Bottom Bun', 1.2, 0.3, (0, 0, 0), bun_material)
cheese = create_cylinder('Cheese', 1.25, 0.1, (0, 0, 0.2), cheese_material)
patty = create_cylinder('Patty', 1.2, 0.3, (0, 0, 0.35), patty_material)
tomato = create_cylinder('Tomato', 1.25, 0.1, (0, 0, 0.55), tomato_material)
lettuce = create_cylinder('Lettuce', 1.3, 0.1, (0, 0, 0.65), lettuce_material)
top_bun = create_top_bun('Top Bun', 1.2, (0, 0, 1), 0.5, bun_material)

# Create sesame seeds
for _ in range(30):
    x_seed = random.uniform(-1.0, 1.0)
    y_seed = random.uniform(-1.0, 1.0)
    if x_seed**2 + y_seed**2 <= 1.0:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(x_seed, y_seed, 1.25))
        seed = bpy.context.object
        seed.scale[2] = 0.2
        seed.data.materials.append(bun_material)


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
