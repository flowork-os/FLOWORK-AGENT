# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, Generate_a_blender_code_to_make_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: Generate a blender code to make a model of blender.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Initialize material properties
materials = {
    'base': (0.2, 0.2, 0.2, 1),  # Dark gray
    'button': (0.8, 0.1, 0.1, 1),  # Red
    'dial': (0.1, 0.1, 0.8, 1),  # Blue
    'jar': (0.8, 0.8, 0.9, 0.3),  # Transparent light blue
    'lid': (0.2, 0.2, 0.2, 1)  # Dark gray
}

# Create materials
for mat_name, color in materials.items():
    mat = bpy.data.materials.new(name=f'Material {mat_name.capitalize()}')
    mat.diffuse_color = color

# Create the base cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.5, location=(0, 0, 0.25))
base_cylinder = bpy.context.object
base_cylinder.name = 'Base'
base_cylinder.data.materials.append(bpy.data.materials['Material Base'])

# Create buttons and dial
for i in range(3):
    bpy.ops.mesh.primitive_cube_add(size=0.1, location=(0.3 * (i - 1), 0.9, 0.5))
    button = bpy.context.object
    button.name = f'Button {i + 1}'
    button.data.materials.append(bpy.data.materials['Material Button'])

bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.05, location=(0, 0.9, 0.55))
dial_cylinder = bpy.context.object

dial_cylinder.name = 'Dial'
dial_cylinder.data.materials.append(bpy.data.materials['Material Dial'])

# Create the jar and lid
bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=2, location=(0, 0, 1.5))
jar_cylinder = bpy.context.object
jar_cylinder.name = 'Jar'
jar_cylinder.data.materials.append(bpy.data.materials['Material Jar'])

bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=0.1, location=(0, 0, 2.55))
lid_cylinder = bpy.context.object
lid_cylinder.name = 'Lid'
lid_cylinder.data.materials.append(bpy.data.materials['Material Lid'])

# Create the center cap
bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.1, location=(0, 0, 2.6))
center_cap_cylinder = bpy.context.object
center_cap_cylinder.name = 'Center Cap'
center_cap_cylinder.data.materials.append(bpy.data.materials['Material Lid'])


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
