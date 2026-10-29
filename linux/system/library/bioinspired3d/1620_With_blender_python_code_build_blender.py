# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, With_blender_python_code_build_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: With blender python code build blender

import bpy

# Clear current mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for the components
container_material = bpy.data.materials.new(name='ContainerMat')
container_material.diffuse_color = (0.8, 0.8, 0.8, 1)
lid_material = bpy.data.materials.new(name='LidMat')
lid_material.diffuse_color = (0.2, 0.2, 0.2, 1)
base_material = bpy.data.materials.new(name='BaseMat')
base_material.diffuse_color = (0.1, 0.1, 0.1, 1)
button_material = bpy.data.materials.new(name='ButtonMat')
button_material.diffuse_color = (0.5, 0.5, 0.5, 1)

# Create the main components
components = []

# Function to add a cylinder
def add_cylinder(radius, depth, position, name, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    components.append(obj)

# Create container, lid, opening, and base
add_cylinder(1, 3, (0, 0, 1.5), 'Container', container_material)
add_cylinder(1.05, 0.2, (0, 0, 3.1), 'Lid', lid_material)
add_cylinder(0.2, 0.2, (0, 0, 3.2), 'Opening', container_material)
add_cylinder(1.2, 0.5, (0, 0, 0.25), 'Base', base_material)

# Create control panel
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 1.1, 0.5))
control_panel = bpy.context.object
control_panel.name = 'ControlPanel'
control_panel.data.materials.append(base_material)

# Generate buttons for the control panel
for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(-0.15 + i * 0.15, 1.15, 0.5))
    button = bpy.context.object
    button.name = f'Button_{i + 1}'
    button.data.materials.append(button_material)


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
