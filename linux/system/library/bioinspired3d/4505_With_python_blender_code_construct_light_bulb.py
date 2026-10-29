# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_python_blender_code_construct_light_bulb" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With python blender code construct light bulb

import bpy

# Remove all existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the components
material_glass = bpy.data.materials.new(name='Glass Material')
material_glass.diffuse_color = (1, 1, 1, 0.1)  # Transparent white color
material_metal = bpy.data.materials.new(name='Metal Material')
material_metal.diffuse_color = (0.5, 0.5, 0.5, 1)  # Gray color for metal

# Create the glass top
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1.5))
glass_object = bpy.context.object
glass_object.name = 'Glass Top'
glass_object.data.materials.append(material_glass)

# Create the screw base
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1, location=(0, 0, 0.5))
screw_object = bpy.context.object
screw_object.name = 'Screw Base'
screw_object.data.materials.append(material_metal)

# Create the filament
bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.02, location=(0, 0, 1.5))
filament_object = bpy.context.object
filament_object.name = 'Filament'
filament_object.data.materials.append(material_metal)


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
