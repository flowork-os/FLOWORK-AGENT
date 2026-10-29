# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, write_code_in_Blender_to_make_spice_containers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: write code in Blender to make spice containers

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with descriptive names
colors = [
    ('Crimson', (1, 0, 0, 1)),
    ('Emerald', (0, 1, 0, 1)),
    ('Azure', (0, 0, 1, 1)),
    ('Lemon', (1, 1, 0, 1))
]

# Function to create a container with a feature

def create_container(index, color):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1, location=(index * 1.5, 0, 0))
    container = bpy.context.object
    container.name = f"Container {index + 1}"
    container.data.materials.append(color)
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(index * 1.5, 0, 0.55))
    feature = bpy.context.object
    feature.name = f"Feature {index + 1}"
    feature.data.materials.append(color)

# Create containers with features
for i, (name, color) in enumerate(colors):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = color
    create_container(i, mat)


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
