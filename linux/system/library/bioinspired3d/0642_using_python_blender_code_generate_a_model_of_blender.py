# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, using_python_blender_code_generate_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: using python blender code generate a model of blender

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the model elements
materials = {
    'base': (0.2, 0.2, 0.2, 1),
    'container': (0.8, 0.8, 0.8, 0.3),
    'button': (0.8, 0.1, 0.1, 1)
}

# Function to create a primitive and assign a material

def add_primitive(primitive_type, **kwargs):
    if primitive_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(**kwargs)
    elif primitive_type == 'cube':
        bpy.ops.mesh.primitive_cube_add(**kwargs)
    obj = bpy.context.object
    return obj

# Create base and container
base = add_primitive('cylinder', radius=1, depth=0.5, location=(0, 0, 0.25))
base.data.materials.append(bpy.data.materials.new(name="Base Material"))
base.data.materials[0].diffuse_color = materials['base']

container = add_primitive('cylinder', radius=0.8, depth=2, location=(0, 0, 1.5))
container.data.materials.append(bpy.data.materials.new(name="Container Material"))
container.data.materials[0].diffuse_color = materials['container']

# Create control buttons
for idx in range(3):
    button = add_primitive('cube', size=0.2, location=(0.5 * (idx - 1), 0.9, 0.25))
    button.name = f"Control Button {idx + 1}"
    button.data.materials.append(bpy.data.materials.new(name="Button Material"))
    button.data.materials[0].diffuse_color = materials['button']


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
