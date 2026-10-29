# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_Blender_code__create_star_icon" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using Blender code, create star icon.

import bpy
import math

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to build a star
def build_star(num_points, outer_radius, inner_radius):
    star_vertices = []
    star_faces = [[i for i in range(num_points * 2)]]
    angle_increment = math.pi / num_points
    for index in range(num_points * 2):
        radius = outer_radius if index % 2 == 0 else inner_radius
        angle = index * angle_increment
        x_coord = radius * math.cos(angle)
        y_coord = radius * math.sin(angle)
        star_vertices.append((x_coord, y_coord, 0))
    return star_vertices, star_faces

# Parameters for the star
points = 5
outer = 1.0
inner = 0.4
vertices, faces = build_star(points, outer, inner)

# Create the mesh and object
mesh = bpy.data.meshes.new(name="StarMesh")
star_object = bpy.data.objects.new("Star", mesh)

# Link the star object to the collection
bpy.context.collection.objects.link(star_object)

# Create the mesh from the vertices and faces
mesh.from_pydata(vertices, [], faces)
mesh.update()

# Create a new material for the star
star_material = bpy.data.materials.new(name="StarMaterial")
star_material.diffuse_color = (1, 1, 0, 1)  # Yellow color
star_object.data.materials.append(star_material)


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
