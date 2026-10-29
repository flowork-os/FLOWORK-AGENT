# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_blender_python_code__construct_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using blender python code, construct a model of blender.

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model
material_base = bpy.data.materials.new(name="Material Base")
material_base.diffuse_color = (0.3, 0.3, 0.3, 1)  # Medium gray color

material_transparent = bpy.data.materials.new(name="Material Transparent")
material_transparent.diffuse_color = (1, 1, 1, 0.2)  # Semi-transparent material
material_transparent.use_nodes = True
nodes_transparent = material_transparent.node_tree.nodes
principled_bsdf = nodes_transparent.get("Principled BSDF")
principled_bsdf.inputs['Alpha'].default_value = 0.2
material_transparent.blend_method = 'BLEND'

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the base, container, and lid
base_obj = create_cylinder(1, 0.5, (0, 0, 0.25), "Base", material_base)
container_obj = create_cylinder(0.8, 2, (0, 0, 1.5), "Container", material_transparent)
lid_obj = create_cylinder(0.85, 0.1, (0, 0, 2.55), "Lid", material_base)


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
