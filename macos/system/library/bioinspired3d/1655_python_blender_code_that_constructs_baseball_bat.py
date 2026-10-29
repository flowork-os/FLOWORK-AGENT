# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, python_blender_code_that_constructs_baseball_bat" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: python blender code that constructs baseball bat.

import bpy

# Clear Existing Mesh Objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a Material for the Bat
bat_material = bpy.data.materials.new(name='BatMaterial')
bat_material.diffuse_color = (0.6, 0.3, 0.1, 1)

# Function to create a cylinder
def create_cylinder(radius, depth, position, name):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(bat_material)
    return obj

# Create the Bat Body
bat_body = create_cylinder(0.05, 1.2, (0, 0, 0.6), 'Bat Body')

# Switch to Edit Mode to Taper the Bat
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
bat_body.data.vertices[0].select = True
bat_body.data.vertices[1].select = True
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.transform.resize(value=(0.5, 0.5, 1))
bpy.ops.object.mode_set(mode='OBJECT')

# Create the Handle Grip
handle_grip = create_cylinder(0.03, 0.3, (0, 0, -0.15), 'Handle Grip')

# Create the Knob for the Handle
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(0, 0, -0.3))
knob = bpy.context.object
knob.name = 'Handle Knob'
knob.data.materials.append(bat_material)


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
