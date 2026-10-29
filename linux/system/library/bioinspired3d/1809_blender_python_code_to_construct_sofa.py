# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_to_construct_sofa" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code to construct sofa

import bpy

# Clear mesh objects from the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a material for the sofa with a different shade
sofa_shade = bpy.data.materials.new(name="SofaShade")
sofa_shade.diffuse_color = (0.6, 0.3, 0.3, 1)  # Slightly different brown color

# Function to create and configure a cube
def setup_cube(size, position, scale_factors, name, mat):
    bpy.ops.mesh.primitive_cube_add(size=size, location=position)
    obj = bpy.context.object
    obj.scale = scale_factors
    obj.name = name
    obj.data.materials.append(mat)

# Create sofa parts
setup_cube(2, (0, 0, 0.5), (2, 1, 0.2), "SofaBase", sofa_shade)
setup_cube(2, (0, -0.9, 1.1), (2, 0.2, 0.7), "SofaBackrest", sofa_shade)

# Generate armrests
for j in range(2):
    setup_cube(2, (2 * (j * 2 - 1), 0, 0.75), (0.2, 1, 0.5), f"SofaArmrest{j + 1}", sofa_shade)

# Generate cushions
for j in range(3):
    setup_cube(2, ((j - 1) * 1.5, 0, 0.75), (0.5, 1, 0.2), f"SofaCushion{j + 1}", sofa_shade)


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
