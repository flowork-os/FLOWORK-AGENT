# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_for_constructing_mandala_design" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code for constructing mandala design.

import bpy
import math

# Clear existing meshes from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials for different colors
material_red = bpy.data.materials.new(name='Red Material')
material_red.diffuse_color = (0.8, 0.2, 0.2, 1)
material_green = bpy.data.materials.new(name='Green Material')
material_green.diffuse_color = (0.2, 0.8, 0.2, 1)
material_blue = bpy.data.materials.new(name='Blue Material')
material_blue.diffuse_color = (0.2, 0.2, 0.8, 1)

# Create the core circle
bpy.ops.mesh.primitive_circle_add(radius=1, location=(0, 0, 0))
core_circle = bpy.context.object
core_circle.name = 'Core Circle'
core_circle.data.materials.append(material_red)

# Create the surrounding rings
for layer in range(1, 4):
    bpy.ops.mesh.primitive_circle_add(radius=layer + 1, location=(0, 0, 0))
    ring_shape = bpy.context.object
    ring_shape.name = f'Ring Layer {layer}'
    ring_shape.data.materials.append(material_green if layer % 2 == 0 else material_blue)

# Generate petals around the core
for petal_index in range(12):
    angle_for_petal = petal_index * (2 * math.pi / 12)
    petal_x = (1.5 + 0.5) * math.cos(angle_for_petal)
    petal_y = (1.5 + 0.5) * math.sin(angle_for_petal)
    bpy.ops.mesh.primitive_circle_add(vertices=5, radius=0.5, location=(petal_x, petal_y, 0), rotation=(0, 0, angle_for_petal))
    petal_object = bpy.context.object
    petal_object.name = f'Petal {petal_index + 1}'
    petal_object.data.materials.append(material_red)

# Add lines radiating outwards
for line_index in range(24):
    angle_for_line = line_index * (2 * math.pi / 24)
    line_x = 3 * math.cos(angle_for_line)
    line_y = 3 * math.sin(angle_for_line)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=3, location=(line_x / 2, line_y / 2, 0), rotation=(0, 0, angle_for_line))
    line_object = bpy.context.object
    line_object.name = f'Line {line_index + 1}'
    line_object.data.materials.append(material_blue)


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
