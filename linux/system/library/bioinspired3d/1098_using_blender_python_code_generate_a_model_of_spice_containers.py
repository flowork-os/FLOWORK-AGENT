# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_blender_python_code_generate_a_model_of_spice_containers" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using blender python code generate a model of spice containers

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a list of colors
color_definitions = [
    ("Red", (1, 0, 0, 1)),
    ("Green", (0, 1, 0, 1)),
    ("Blue", (0, 0, 1, 1)),
    ("Yellow", (1, 1, 0, 1))
]

# Class to encapsulate the creation of containers
class Container:
    def __init__(self, index, color):
        self.index = index
        self.color = color
        self.create_container()

    def create_container(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1, location=(self.index * 1.5, 0, 0))
        cylinder = bpy.context.object
        cylinder.name = f"Container {self.index + 1}"
        cylinder.data.materials.append(self.color)
        
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(self.index * 1.5, 0, 0.55))
        sphere = bpy.context.object
        sphere.name = f"Feature {self.index + 1}"
        sphere.data.materials.append(self.color)

# Generate materials and create containers
for i, (name, rgba) in enumerate(color_definitions):
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = rgba
    Container(i, mat)


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
