# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Make_blender_in_python_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Make blender in python blender code

import bpy

# Clear the scene by deselecting and deleting all mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the model components
mat_base = bpy.data.materials.new(name='BaseMaterial')
mat_base.diffuse_color = (0.2, 0.2, 0.2, 1.0)
mat_jar = bpy.data.materials.new(name='JarMaterial')
mat_jar.diffuse_color = (0.8, 0.8, 0.8, 0.3)
mat_lid = bpy.data.materials.new(name='LidMaterial')
mat_lid.diffuse_color = (0.1, 0.1, 0.1, 1.0)
mat_panel = bpy.data.materials.new(name='PanelMaterial')
mat_panel.diffuse_color = (0.5, 0.5, 0.5, 1.0)

# Create geometry components
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1, location=(0, 0, 0.5))
base_object = bpy.context.object
base_object.name = 'Base'
base_object.data.materials.append(mat_base)

bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0.75, 0.25))
panel_object = bpy.context.object
panel_object.name = 'Control Panel'
panel_object.scale = (0.5, 0.1, 0.5)
panel_object.data.materials.append(mat_panel)

bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=2, location=(0, 0, 2))
jar_object = bpy.context.object
jar_object.name = 'Jar'
jar_object.data.materials.append(mat_jar)

bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=0.1, location=(0, 0, 3.05))
lid_object = bpy.context.object
lid_object.name = 'Lid'
lid_object.data.materials.append(mat_lid)

# Add markings to the jar
for i in range(1, 5):
    bpy.ops.mesh.primitive_cube_add(size=0.05, location=(0.85, 0, 1 + i * 0.4))
    marking_object = bpy.context.object
    marking_object.name = f'Marking_{i}'
    marking_object.scale = (0.02, 0.02, 0.2)
    marking_object.data.materials.append(mat_base)


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
