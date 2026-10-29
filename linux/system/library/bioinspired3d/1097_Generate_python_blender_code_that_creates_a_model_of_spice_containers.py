# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_python_blender_code_that_creates_a_model_of_spice_containers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate python blender code that creates a model of spice containers.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize material colors
material_names = ['Red', 'Green', 'Blue', 'Yellow']
material_values = [(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), (1, 1, 0, 1)]

# Create materials and store them in a dictionary
materials = {name: bpy.data.materials.new(name=name) for name, value in zip(material_names, material_values)}
for name, value in zip(material_names, material_values):
    materials[name].diffuse_color = value

# Function to generate a cylinder and sphere

def generate_shapes(index, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1, location=(index * 1.5, 0, 0))
    cylinder = bpy.context.object
    cylinder.name = f"Container {index + 1}"
    cylinder.data.materials.append(mat)
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(index * 1.5, 0, 0.55))
    sphere = bpy.context.object
    sphere.name = f"Feature {index + 1}"
    sphere.data.materials.append(mat)

# Create shapes for each color
for idx, (name, mat) in enumerate(materials.items()):
    generate_shapes(idx, mat)


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
