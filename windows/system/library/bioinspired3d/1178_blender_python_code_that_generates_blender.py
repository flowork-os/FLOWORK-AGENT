# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, blender_python_code_that_generates_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: blender python code that generates blender

import bpy

# Clear existing mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials with descriptive names
material_base = bpy.data.materials.new(name='Material Base')
material_base.diffuse_color = (0.3, 0.3, 0.3, 1)  # Medium gray
material_button = bpy.data.materials.new(name='Material Button')
material_button.diffuse_color = (0.9, 0.2, 0.2, 1)  # Bright red
material_dial = bpy.data.materials.new(name='Material Dial')
material_dial.diffuse_color = (0.2, 0.2, 0.9, 1)  # Bright blue
material_jar = bpy.data.materials.new(name='Material Jar')
material_jar.diffuse_color = (0.9, 0.9, 0.95, 0.4)  # Light transparent blue
material_lid = bpy.data.materials.new(name='Material Lid')
material_lid.diffuse_color = (0.3, 0.3, 0.3, 1)  # Medium gray

# Function to create a cylinder

def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Create the base
base_object = create_cylinder(1, 0.5, (0, 0, 0.25), 'Base', material_base)

# Create buttons
for index in range(3):
    create_cylinder(0.05, 0.1, (0.3 * (index - 1), 0.9, 0.5), f'Button {index + 1}', material_button)

# Create the dial
create_cylinder(0.1, 0.05, (0, 0.9, 0.55), 'Dial', material_dial)

# Create the jar
create_cylinder(0.8, 2, (0, 0, 1.5), 'Jar', material_jar)

# Create the lid
create_cylinder(0.85, 0.1, (0, 0, 2.55), 'Lid', material_lid)

# Create the center cap
create_cylinder(0.2, 0.1, (0, 0, 2.6), 'Center Cap', material_lid)


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
