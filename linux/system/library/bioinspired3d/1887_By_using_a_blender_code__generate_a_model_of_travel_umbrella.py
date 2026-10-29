# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_a_blender_code__generate_a_model_of_travel_umbrella" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using a blender code, generate a model of travel umbrella.

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create materials
canopy_mat = bpy.data.materials.new(name='CanopyMaterial')
canopy_mat.diffuse_color = (0.7, 0.3, 0.3, 1)  # Soft red for the canopy
shaft_mat = bpy.data.materials.new(name='ShaftMaterial')
shaft_mat.diffuse_color = (0.5, 0.5, 0.5, 1)  # Neutral gray for the shaft

# Function to generate the entire model
def generate_model():
    # Add a cone for the canopy
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1, depth=0.5, location=(0, 0, 0.25))
    cone = bpy.context.object
    cone.name = 'Canopy'
    cone.data.materials.append(canopy_mat)
    
    # Add a cylinder for the shaft
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(0, 0, -1))
    cylinder = bpy.context.object
    cylinder.name = 'Shaft'
    cylinder.data.materials.append(shaft_mat)
    
    # Add another cylinder for the handle
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.5, location=(0, 0, -2.25))
    handle_cyl = bpy.context.object
    handle_cyl.name = 'Handle'
    handle_cyl.data.materials.append(shaft_mat)

# Execute model generation
generate_model()


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
