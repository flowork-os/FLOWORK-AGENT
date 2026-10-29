# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_model_of_sofa_using_blender_script" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a model of sofa using blender script

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define a new material for the sofa
material_for_sofa = bpy.data.materials.new(name='SofaColor')
material_for_sofa.diffuse_color = (0.5, 0.25, 0.25, 1)  # Medium brown color

# Function to create a sofa component
def create_sofa_component(size, position, component_name, dimensions, material):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    component = bpy.context.object
    component.name = component_name
    component.scale = dimensions
    component.data.materials.append(material)

# Build the sofa parts
create_sofa_component(2, (0, 0, 0.5), 'Base', (2, 1, 0.2), material_for_sofa)
create_sofa_component(2, (0, -0.9, 1.1), 'Backrest', (2, 0.1, 0.6), material_for_sofa)

# Create armrests using a loop
for i in range(2):
    x_coord = 1.9 * (i * 2 - 1)
    create_sofa_component(2, (x_coord, 0, 0.7), f'Armrest{i + 1}', (0.1, 1, 0.4), material_for_sofa)


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
