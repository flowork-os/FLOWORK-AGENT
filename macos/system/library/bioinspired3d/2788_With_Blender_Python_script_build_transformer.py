# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_Blender_Python_script_build_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With Blender Python script build transformer.

import bpy

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
materials = {
    'core': bpy.data.materials.new(name='Main Body Material'),
    'coil': bpy.data.materials.new(name='Spiral Material')
}
materials['core'].diffuse_color = (0.15, 0.15, 0.15, 1)  # Dark gray
materials['coil'].diffuse_color = (0.85, 0.55, 0.25, 1)  # Copper-like color

# Create the main body of the model
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=1.0, location=(0, 0, 0))
main_body = bpy.context.object
main_body.name = 'Main Body'
main_body.data.materials.append(materials['core'])

# Generate coils
for i in range(3):
    z_position = -0.3 + i * 0.3
    bpy.ops.mesh.primitive_torus_add(align='WORLD', location=(0, 0, z_position), major_radius=0.35, minor_radius=0.05)
    spiral = bpy.context.object
    spiral.name = f'Spiral {i + 1}'
    spiral.data.materials.append(materials['coil'])


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
