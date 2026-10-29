# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Blender_code_to_build_a_model_of_power_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Blender code to build a model of power transformer

import bpy
import math

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for different parts
materials = {
    'base': bpy.data.materials.new(name='BaseMaterial'),
    'core': bpy.data.materials.new(name='CoreMaterial'),
    'coil': bpy.data.materials.new(name='CoilMaterial'),
    'terminal': bpy.data.materials.new(name='TerminalMaterial')
}
materials['base'].diffuse_color = (0.5, 0.5, 0.5, 1)
materials['core'].diffuse_color = (0.2, 0.2, 0.2, 1)
materials['coil'].diffuse_color = (0.8, 0.8, 0.8, 1)
materials['terminal'].diffuse_color = (0.9, 0.9, 0.9, 1)

# Function to create a mesh object

def create_mesh(primitive_type, **kwargs):
    bpy.ops.mesh.primitive_cube_add(size=kwargs.get('size', 1), location=kwargs.get('location', (0, 0, 0)))
    obj = bpy.context.object
    obj.name = kwargs.get('name', 'Object')
    obj.data.materials.append(kwargs.get('material'))
    return obj

# Create the base object
base_object = create_mesh('cube', size=2, location=(0, 0, 0.5), name='Base', material=materials['base'])
base_object.scale[2] = 0.1

# Create the core object
core_object = create_mesh('cylinder', radius=0.3, depth=1.5, location=(0, 0, 1.25), name='Core', material=materials['core'])

# Create coils using a loop
for index in range(8):
    theta = index * (math.pi / 4)
    x_coord = 0.6 * math.cos(theta)
    y_coord = 0.6 * math.sin(theta)
    coil = create_mesh('torus', major_radius=0.4, minor_radius=0.05, location=(x_coord, y_coord, 1.25), name=f'Coil_{index + 1}', material=materials['coil'])

# Create terminal objects
for idx in range(2):
    terminal_x = 0.7 * (idx * 2 - 1)
    terminal_object = create_mesh('cylinder', radius=0.05, depth=0.2, location=(terminal_x, 0, 1.5), name=f'Terminal_{idx + 1}', material=materials['terminal'])


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
