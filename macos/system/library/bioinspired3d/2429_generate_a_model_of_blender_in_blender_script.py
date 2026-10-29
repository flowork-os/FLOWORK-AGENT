# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_blender_in_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of blender in blender script

import bpy

# Reset the scene by removing all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create new materials for the model
mat_base = bpy.data.materials.new(name="Base Material")
mat_base.diffuse_color = (0.1, 0.1, 0.1, 1)  # Darker gray color

mat_container = bpy.data.materials.new(name="Container Material")
mat_container.diffuse_color = (1, 1, 1, 0.15)  # Slightly transparent material
mat_container.use_nodes = True

# Configure the transparency node
container_nodes = mat_container.node_tree.nodes
bsdf_node = container_nodes.get("Principled BSDF")
bsdf_node.inputs['Alpha'].default_value = 0.15
mat_container.blend_method = 'BLEND'

# Adding cylinders with specific parameters
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
base_cylinder = bpy.context.object
base_cylinder.name = "Base"
base_cylinder.data.materials.append(mat_base)

bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=2, location=(0, 0, 1.5))
container_cylinder = bpy.context.object
container_cylinder.name = "Container"
container_cylinder.data.materials.append(mat_container)

bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=0.1, location=(0, 0, 2.55))
lid_cylinder = bpy.context.object
lid_cylinder.name = "Lid"
lid_cylinder.data.materials.append(mat_base)


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
