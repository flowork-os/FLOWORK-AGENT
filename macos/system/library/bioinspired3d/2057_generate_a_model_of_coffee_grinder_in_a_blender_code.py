# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, generate_a_model_of_coffee_grinder_in_a_blender_code" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: generate a model of coffee grinder in a blender code

import bpy

# Clear existing mesh objects
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define new materials
metallic_surface = bpy.data.materials.new(name="Metal Surface")
metallic_surface.diffuse_color = (0.5, 0.5, 0.5, 1)
wooden_surface = bpy.data.materials.new(name="Wood Surface")
wooden_surface.diffuse_color = (0.55, 0.27, 0.07, 1)

# Create a class for the model components
class ModelComponent:
    def __init__(self, shape_type, **kwargs):
        self.shape_type = shape_type
        self.kwargs = kwargs
        self.object = self.create_shape()

    def create_shape(self):
        if self.shape_type == 'cube':
            bpy.ops.mesh.primitive_cube_add(**self.kwargs)
        elif self.shape_type == 'cylinder':
            bpy.ops.mesh.primitive_cylinder_add(**self.kwargs)
        elif self.shape_type == 'sphere':
            bpy.ops.mesh.primitive_uv_sphere_add(**self.kwargs)
        return bpy.context.object

# Create components using the class
base_component = ModelComponent('cube', size=2, location=(0, 0, 1))
base_component.object.name = "Base"
base_component.object.data.materials.append(wooden_surface)

container_component = ModelComponent('cylinder', radius=0.75, depth=1.5, location=(0, 0, 2.75))
container_component.object.name = "Bean Container"
container_component.object.data.materials.append(metallic_surface)

knob_component = ModelComponent('cylinder', radius=0.2, depth=0.1, location=(0, 0, 3.55))
knob_component.object.name = "Grind Setting Knob"
knob_component.object.data.materials.append(metallic_surface)

handle_component = ModelComponent('cylinder', radius=0.05, depth=1, location=(1, 0, 3), rotation=(0, 1.57, 0))
handle_component.object.name = "Handle"
handle_component.object.data.materials.append(wooden_surface)

handle_knob_component = ModelComponent('sphere', radius=0.1, location=(1.5, 0, 3))
handle_knob_component.object.name = "Handle Knob"
handle_knob_component.object.data.materials.append(wooden_surface)


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
