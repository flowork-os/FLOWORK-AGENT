# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, make_a_model_of_transformer_using_a_Blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: make a model of transformer using a Blender code

import bpy

# Clear the scene of all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material creation for the core and coils
core_mat = bpy.data.materials.new(name='Core Material')
core_mat.diffuse_color = (0.2, 0.2, 0.2, 1)  # Dark gray
coil_mat = bpy.data.materials.new(name='Coil Material')
coil_mat.diffuse_color = (0.8, 0.5, 0.2, 1)  # Copper-like shade

# Main function to create the 3D model
def build_model():
    # Create core
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.0, location=(0, 0, 0))
    core = bpy.context.object
    core.name = 'Central Cylinder'
    core.data.materials.append(core_mat)
    
    # Create coils
    for i in range(3):
        z_coord = -0.3 + i * 0.3
        bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(0, 0, z_coord), major_radius=0.35, minor_radius=0.05)
        coil = bpy.context.object
        coil.name = f'Coil Segment {i + 1}'
        coil.data.materials.append(coil_mat)

# Call the main function to build the model
build_model()


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
