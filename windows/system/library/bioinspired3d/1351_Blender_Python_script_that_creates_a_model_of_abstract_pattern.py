# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_Python_script_that_creates_a_model_of_abstract_pattern" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender Python script that creates a model of abstract pattern

import bpy
import math

# Clear the scene of mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new material with a gray color
material_instance = bpy.data.materials.new(name='Mid Gray')
material_instance.diffuse_color = (0.5, 0.5, 0.5, 1)

# Function to generate shapes

def generate_shapes():
    for idx in range(5):
        phi = idx * math.pi / 5
        # Generating torus
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.1, location=(math.cos(phi), math.sin(phi), 0))
        torus_obj = bpy.context.object
        torus_obj.name = f'Torus_{idx + 1}'
        torus_obj.data.materials.append(material_instance)

        # Generating cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(math.cos(phi), math.sin(phi), 0), rotation=(0, 0, phi))
        cylinder_obj = bpy.context.object
        cylinder_obj.name = f'Cyl_{idx + 1}'
        cylinder_obj.data.materials.append(material_instance)

        # Generating sphere
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(math.cos(phi), math.sin(phi), 0))
        sphere_obj = bpy.context.object
        sphere_obj.name = f'Sphere_{idx + 1}'
        sphere_obj.data.materials.append(material_instance)

# Call function to create shapes
generate_shapes()


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
