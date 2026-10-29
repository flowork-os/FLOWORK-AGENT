# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, by_using_Blender_code__generate_a_model_of_modular_shelving" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: by using Blender code, generate a model of modular shelving

import bpy

# Clear all existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a material
def create_material(name, color):
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = color
    return material

# Create the material for the shelves
material_for_shelves = create_material("ShelfMaterial", (0.9, 0.9, 0.9, 1))  # Bright gray color

# Function to create shelves
def create_shelves(num_shelves, height, width, depth):
    for i in range(num_shelves):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, i * (height + 0.5)))
        shelf = bpy.context.object
        shelf.scale = (width, depth, height)
        shelf.name = f"Shelf_{i + 1}"
        shelf.data.materials.append(material_for_shelves)

create_shelves(3, 0.1, 2, 0.5)

# Function to create supports
def create_supports(num_supports, radius, height):
    for i in range(num_supports):
        x_pos = (i % 2) * 2 - 1  # Adjusted for centering
        y_pos = (i // 2) * 0.5 - 0.25  # Adjusted for centering
        bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=(x_pos, y_pos, height / 2))
        support = bpy.context.object
        support.name = f"Support_{i + 1}"
        support.data.materials.append(material_for_shelves)

create_supports(4, 0.05, 2)


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
