# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_sofa_in_Blender_Python_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of sofa in Blender Python script

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a material for the sofa
material_for_sofa = bpy.data.materials.new(name='MaterialForSofa')
material_for_sofa.diffuse_color = (0.4, 0.2, 0.1, 1)  # A slightly darker brown color

# Create the sofa components using a loop
component_data = [
    {'name': 'Base', 'location': (0, 0, 0.5), 'scale': (2, 1, 0.2)},
    {'name': 'Backrest', 'location': (0, -1, 1.1), 'scale': (2, 0.2, 0.6)},
]

# Function to create and assign material to a new mesh object

def create_mesh(name, loc, scl):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    mesh_object = bpy.context.object
    mesh_object.scale = scl
    mesh_object.name = name
    mesh_object.data.materials.append(material_for_sofa)

# Create base and backrest
for component in component_data:
    create_mesh(component['name'], component['location'], component['scale'])

# Create armrests
for i in range(2):
    x_position = 1.8 * (i * 2 - 1)
    create_mesh(f'Armrest_{i + 1}', (x_position, 0, 0.8), (0.2, 1, 0.4))

# Create cushions
for i in range(3):
    cushion_x = (i - 1) * 1.2
    create_mesh(f'Cushion_{i + 1}', (cushion_x, 0, 0.7), (0.4, 1, 0.2))


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
