# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_code_in_Blender__construct_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With code in Blender, construct blender

import bpy

# Start by clearing the current scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Material definitions
material_base = bpy.data.materials.new(name="BaseMaterial")
material_base.diffuse_color = (0.1, 0.1, 0.1, 1)
material_pitcher = bpy.data.materials.new(name="PitcherMaterial")
material_pitcher.diffuse_color = (0.8, 0.8, 0.8, 0.3)
material_lid = bpy.data.materials.new(name="LidMaterial")
material_lid.diffuse_color = (0.1, 0.1, 0.1, 1)

# Create geometrical components
components = [
    (0.5, 0.3, (0, 0, 0.15), "Base", material_base),
    (0.4, 1, (0, 0, 0.8), "Pitcher", material_pitcher),
    (0.42, 0.1, (0, 0, 1.35), "Lid", material_lid)
]

for radius, depth, location, name, material in components:
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)

# Adding measurement lines
for i in range(3):
    bpy.ops.mesh.primitive_plane_add(size=0.02, location=(0.4, 0, 0.6 + i * 0.3))
    line = bpy.context.object
    line.name = f"Measurement Line {i + 1}"
    line.scale[1] = 5
    line.data.materials.append(material_base)


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
