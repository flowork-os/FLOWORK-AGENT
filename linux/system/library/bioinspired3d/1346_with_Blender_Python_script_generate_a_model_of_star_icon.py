# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, with_Blender_Python_script_generate_a_model_of_star_icon" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: with Blender Python script generate a model of star icon.

import bpy
import math

# Remove all mesh objects in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Class to generate a star object
class StarShape:
    def __init__(self, points, outer_rad, inner_rad):
        self.points = points
        self.outer_radius = outer_rad
        self.inner_radius = inner_rad
        self.vertices = []
        self.faces = []
        self.create_vertices()

    def create_vertices(self):
        angle = math.pi / self.points
        for i in range(self.points * 2):
            radius = self.outer_radius if i % 2 == 0 else self.inner_radius
            theta = i * angle
            x = radius * math.cos(theta)
            y = radius * math.sin(theta)
            self.vertices.append((x, y, 0))
        self.faces.append([i for i in range(self.points * 2)])

# Instantiate the star shape
star = StarShape(5, 1.0, 0.4)

# Create mesh and object
mesh_data = bpy.data.meshes.new(name="Star")
star_object = bpy.data.objects.new("Star", mesh_data)

# Link the star object to the scene
bpy.context.collection.objects.link(star_object)

# Generate the mesh
mesh_data.from_pydata(star.vertices, [], star.faces)
mesh_data.update()

# Create and assign a material to the star
material = bpy.data.materials.new(name="StarColor")
material.diffuse_color = (1, 1, 0, 1)  # Yellow
star_object.data.materials.append(material)


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
