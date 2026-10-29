# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, code_in_Blender_that_constructs_a_model_of_blender" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: code in Blender that constructs a model of blender.

import bpy

# Step 1: Clear the Scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for the model
base_mat = bpy.data.materials.new(name="Base Material")
base_mat.diffuse_color = (0.3, 0.3, 0.3, 1)  # Medium gray for the base
control_mat = bpy.data.materials.new(name="Control Material")
control_mat.diffuse_color = (0.05, 0.05, 0.05, 1)  # Almost black for the control panel
jar_mat = bpy.data.materials.new(name="Jar Material")
jar_mat.diffuse_color = (1, 1, 1, 0.2)  # Slightly more opaque transparent color for the jar
lid_mat = bpy.data.materials.new(name="Lid Material")
lid_mat.diffuse_color = (0.3, 0.3, 0.3, 1)  # Medium gray for the lid

# Function to create a cylinder
def create_cylinder(radius, depth, location, name, material):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj

# Step 2: Create the Base
create_cylinder(1, 0.5, (0, 0, 0.25), "Base", base_mat)

# Step 3: Create the Control Panel
bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0.75, 0.25))
control_panel = bpy.context.object
control_panel.name = "Control Panel"
control_panel.scale[2] = 0.15  # Make the control panel thinner
control_panel.data.materials.append(control_mat)

# Step 4: Create the Blending Jar
create_cylinder(0.8, 2, (0, 0, 1.5), "Jar", jar_mat)

# Step 5: Create the Lid
create_cylinder(0.85, 0.1, (0, 0, 2.55), "Lid", lid_mat)


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
