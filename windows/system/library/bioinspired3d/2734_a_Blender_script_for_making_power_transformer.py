# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, a_Blender_script_for_making_power_transformer" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: a Blender script for making power transformer

import bpy

# Remove all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Define materials for different parts of the model
material_core = bpy.data.materials.new(name='MaterialCore')
material_core.diffuse_color = (0.5, 0.5, 0.5, 1)  # Core color
material_coil = bpy.data.materials.new(name='MaterialCoil')
material_coil.diffuse_color = (1, 0.6, 0, 1)  # Coil color
material_terminal = bpy.data.materials.new(name='MaterialTerminal')
material_terminal.diffuse_color = (0, 0, 0, 1)  # Terminal color

# Object-oriented approach
class ModelComponent:
    def __init__(self, obj_type, dimensions, location, name, material):
        self.obj_type = obj_type
        self.dimensions = dimensions
        self.location = location
        self.name = name
        self.material = material
        self.create_object()

    def create_object(self):
        if self.obj_type == 'cylinder':
            bpy.ops.mesh.primitive_cylinder_add(radius=self.dimensions[0], depth=self.dimensions[1], location=self.location)
        elif self.obj_type == 'torus':
            bpy.ops.mesh.primitive_torus_add(major_radius=self.dimensions[0], minor_radius=self.dimensions[1], location=self.location)
        obj = bpy.context.object
        obj.name = self.name
        obj.data.materials.append(self.material)

# Create core
ModelComponent('cylinder', (0.3, 2), (0, 0, 0), 'Core', material_core)

# Create coils
for i in range(2):
    z_position = 0.5 * (i * 2 - 1)
    ModelComponent('torus', (0.4, 0.05), (0, 0, z_position), f'Coil_{i + 1}', material_coil)

# Create terminals
for i in range(2):
    x_position = 0.2 * (i * 2 - 1)
    ModelComponent('cylinder', (0.05, 0.2), (x_position, 0, 1.1), f'Terminal_{i + 1}', material_terminal)


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
