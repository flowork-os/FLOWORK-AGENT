# [FL_INDEX: keywords="bioinspired_3d, bpy, bmesh, procedural_biology, By_using_python_blender_code_create_spiral_staircase" | COT="Bio-inspired 3D procedural generator from 3DCodeverse"]
# Structure: By using python blender code create spiral staircase

import bpy
import math

# Clear all mesh objects from the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Function to create a pole

def create_pole(radius, height, position):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=position)
    return bpy.context.object

# Function to create a step

def create_step(location, rotation):
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=location)
    step = bpy.context.object
    step.rotation_euler[2] = rotation
    return step

# Create the central pole
pole = create_pole(0.1, 5, (0, 0, 2.5))
pole.name = 'Central Support'

# Generate steps around the pole
steps_count = 20
step_height = 0.2
step_radius = 1.0

for i in range(steps_count):
    angle = i * (2 * math.pi / steps_count)
    x = step_radius * math.cos(angle)
    y = step_radius * math.sin(angle)
    z = i * step_height
    step = create_step((x, y, z), angle)
    step.name = f'Step_{i + 1}'

# Create the handrail
bpy.ops.curve.primitive_bezier_circle_add(radius=0.05)
rail_profile = bpy.context.object
rail_profile.name = 'Railing'

bpy.ops.curve.primitive_bezier_curve_add()
handrail = bpy.context.object
handrail.name = 'Handrail'
handrail.data.splines.clear()

spline = handrail.data.splines.new(type='BEZIER')
spline.bezier_points.add(steps_count - 1)

for i in range(steps_count):
    angle = i * (2 * math.pi / steps_count)
    x = (step_radius + 0.25) * math.cos(angle)
    y = (step_radius + 0.25) * math.sin(angle)
    z = i * step_height
    spline.bezier_points[i].co = (x, y, z)
    spline.bezier_points[i].handle_left_type = 'AUTO'
    spline.bezier_points[i].handle_right_type = 'AUTO'

handrail.data.bevel_object = rail_profile
handrail.data.fill_mode = 'FULL'
