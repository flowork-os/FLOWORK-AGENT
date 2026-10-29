# [FL_INDEX: keywords="blender_factory, procedural_3d, SpiderPlantFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SpiderPlantFactory | Category: factories_geo
# Prompt: A 3D model of a spider plant rendered from an elevated perspective, featuring a dense spherical rosette of numerous long narrow blade-like leaves radiating outward and slightly downward from a central growth point, colored in yellow-green with lighter edges along each leaf.

import os
import math
import colorsys
import random
import bpy
import numpy as np
from numpy.random import normal, randint, uniform

# ──────────────────────────────────────────────────────────
# Seed infrastructure
# ──────────────────────────────────────────────────────────
SEED = int(os.environ.get("SEED", 0))

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

def _hsv2rgba(h, s, v):
    h = h - math.floor(h)
    s = max(0.0, min(1.0, float(s)))
    v = max(0.0, min(1.0, float(v)))
    r, g, b = colorsys.hsv_to_rgb(float(h), s, v)
    return (r, g, b, 1.0)

# ============================================================================
# Inlined material — hand-crafted for SpiderPlantFactory
# shader_spider_plant: PrincipledBSDF + TranslucentBSDF mixed via MixShader
# ============================================================================

def make_spider_plant_material(name="SpiderPlantMaterial"):
    """Faithful raw-bpy reproduction of shader_spider_plant.

    Consumes numpy.random in the same order as the original:
      main_hsv_color: uniform(0.18, 0.36), uniform(0.70, 0.90), uniform(0.2, 0.3)
    """

    main_hue = float(np.random.uniform(0.18, 0.36))
    main_sat = float(np.random.uniform(0.70, 0.90))
    main_val = float(np.random.uniform(0.2, 0.3))
    main_color = _hsv2rgba(main_hue, main_sat, main_val)

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    node_tree = mat.node_tree
    node_tree.nodes.clear()

    # PrincipledBSDF
    principled = node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = main_color
    principled.inputs["IOR"].default_value = 1.01
    principled.inputs["Roughness"].default_value = 2.0

    # TranslucentBSDF
    translucent = node_tree.nodes.new("ShaderNodeBsdfTranslucent")
    translucent.inputs["Color"].default_value = main_color

    # MixShader (Factor defaults to 0.5)
    mix_shader = node_tree.nodes.new("ShaderNodeMixShader")
    node_tree.links.new(principled.outputs["BSDF"], mix_shader.inputs[1])
    node_tree.links.new(translucent.outputs["BSDF"], mix_shader.inputs[2])

    # MaterialOutput
    mat_output = node_tree.nodes.new("ShaderNodeOutputMaterial")
    node_tree.links.new(mix_shader.outputs["Shader"], mat_output.inputs["Surface"])

    return mat


seed_all(SEED)
MAT_SPIDER_PLANT = make_spider_plant_material("SpiderPlant_Material")
MAT_SPIDER_PLANT.use_fake_user = True

# No wear_tear for this factory


# ============================================================================
# ============================================================================
np.random.seed(SEED)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
bpy.context.scene.cursor.location = (0, 0, 0)

# --------------- helpers ---------------
def assign_curve(fc_node, points, handles=None):
    """Set control points on a ShaderNodeFloatCurve node."""

    curve = fc_node.mapping.curves[0]
    for i, (x, y) in enumerate(points):
        if i < len(curve.points):
            curve.points[i].location = (x, y)
        else:
            curve.points.new(x, y)
    if handles:
        for i, h in enumerate(handles):
            if i < len(curve.points):
                curve.points[i].handle_type = h
    fc_node.mapping.update()

# --------------- build leaf geometry node group ---------------
def build_leaf_geometry_ng(idx):
    """Build one leaf geometry variant.
    Pipeline: QuadraticBezier -> X rotation -> Z rotation -> CaptureAttribute(spline factor)
    -> CaptureAttribute(normal) -> contour width -> SetPosition -> CurveToMesh
    -> ExtrudeMesh(EDGES, normal, width)
    """

    name = f'spider_leaf_{idx}'
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Mesh', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    go = ng.nodes.new('NodeGroupOutput')

    # QuadraticBezier: straight vertical curve
    qb = ng.nodes.new('GeometryNodeCurveQuadraticBezier')
    qb.inputs[0].default_value = 100   # Resolution
    qb.inputs[1].default_value = (0.0, 0.0, 0.0)
    qb.inputs[2].default_value = (0.0, 0.0, 0.5)
    qb.inputs[3].default_value = (0.0, 0.0, 1.0)

    # X rotation (curl along spline)
    pos_x = ng.nodes.new('GeometryNodeInputPosition')
    sp_x = ng.nodes.new('GeometryNodeSplineParameter')
    mr_x = ng.nodes.new('ShaderNodeMapRange')
    mr_x.inputs[4].default_value = np.abs(normal(0, 1.2))   # To Max
    ng.links.new(sp_x.outputs[0], mr_x.inputs[0])           # Factor -> Value

    vr_x = ng.nodes.new('ShaderNodeVectorRotate')
    vr_x.rotation_type = 'X_AXIS'
    vr_x.inputs[1].default_value = (0.0, 0.0, 0.5)          # Center
    ng.links.new(pos_x.outputs[0], vr_x.inputs[0])
    ng.links.new(mr_x.outputs[0], vr_x.inputs[3])

    sp1 = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(qb.outputs[0], sp1.inputs[0])
    ng.links.new(vr_x.outputs[0], sp1.inputs[3])

    # Z rotation (twist along spline)
    pos_z = ng.nodes.new('GeometryNodeInputPosition')
    sp_z = ng.nodes.new('GeometryNodeSplineParameter')
    mr_z = ng.nodes.new('ShaderNodeMapRange')
    mr_z.inputs[4].default_value = np.abs(normal(0, 0.6))   # To Max
    ng.links.new(sp_z.outputs[0], mr_z.inputs[0])

    vr_z = ng.nodes.new('ShaderNodeVectorRotate')
    vr_z.rotation_type = 'Z_AXIS'
    vr_z.inputs[1].default_value = (0.0, 0.0, 0.5)
    ng.links.new(pos_z.outputs[0], vr_z.inputs[0])
    ng.links.new(mr_z.outputs[0], vr_z.inputs[3])

    sp2 = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(sp1.outputs[0], sp2.inputs[0])
    ng.links.new(vr_z.outputs[0], sp2.inputs[3])

    # Capture spline parameter factor
    sp_cap = ng.nodes.new('GeometryNodeSplineParameter')
    ca_sp = ng.nodes.new('GeometryNodeCaptureAttribute')
    ca_sp.capture_items.new('FLOAT', 'SplineFactor')
    ng.links.new(sp2.outputs[0], ca_sp.inputs[0])
    ng.links.new(sp_cap.outputs[0], ca_sp.inputs[1])

    # Capture normal
    inp_norm = ng.nodes.new('GeometryNodeInputNormal')
    ca_n = ng.nodes.new('GeometryNodeCaptureAttribute')
    ca_n.capture_items.new('VECTOR', 'Normal')
    ng.links.new(ca_sp.outputs[0], ca_n.inputs[0])
    ng.links.new(inp_norm.outputs[0], ca_n.inputs[1])

    # Leaf contour width profile
    k = uniform(0, 0.05)
    fc_w = ng.nodes.new('ShaderNodeFloatCurve')
    ng.links.new(ca_sp.outputs[1], fc_w.inputs[1])
    assign_curve(fc_w, [
        (0.0, 0.1),
        (0.2, 0.1 + k / 1.5),
        (0.4, 0.1 + k / 1.5),
        (0.6, 0.1),
        (0.8, 0.1 - k),
        (1.0, 0.0),
    ], handles=['AUTO', 'AUTO', 'AUTO', 'AUTO', 'AUTO', 'VECTOR'])

    mul_w = ng.nodes.new('ShaderNodeMath')
    mul_w.operation = 'MULTIPLY'
    mul_w.inputs[1].default_value = uniform(0.8, 1.3)
    ng.links.new(fc_w.outputs[0], mul_w.inputs[0])

    cxyz = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(mul_w.outputs[0], cxyz.inputs[0])    # X

    sp3 = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(ca_n.outputs[0], sp3.inputs[0])
    ng.links.new(cxyz.outputs[0], sp3.inputs[3])

    # CurveToMesh + ExtrudeMesh(EDGES)
    c2m = ng.nodes.new('GeometryNodeCurveToMesh')
    c2m.inputs[3].default_value = True                 # Fill Caps
    ng.links.new(sp3.outputs[0], c2m.inputs[0])

    ext = ng.nodes.new('GeometryNodeExtrudeMesh')
    ext.mode = 'EDGES'
    ng.links.new(c2m.outputs[0], ext.inputs[0])
    ng.links.new(ca_n.outputs[1], ext.inputs[2])       # Offset (normal)
    ng.links.new(mul_w.outputs[0], ext.inputs[3])      # Offset Scale

    ng.links.new(ext.outputs[0], go.inputs[0])
    return ng

# --------------- build leaf rotation node groups ---------------
def build_leaf_rotate_on_base_ng(x_R):
    """Rotation vector for leaf on base circle: (x_R+rand, rand_y, noise_z)."""

    name = f'leaf_rot_{id(x_R)}'
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Vector', in_out='OUTPUT', socket_type='NodeSocketVector')
    go = ng.nodes.new('NodeGroupOutput')

    rv_x = ng.nodes.new('FunctionNodeRandomValue')
    rv_x.data_type = 'FLOAT'
    rv_x.inputs[2].default_value = -0.3
    rv_x.inputs[3].default_value = 0.3

    add_x = ng.nodes.new('ShaderNodeMath')
    add_x.operation = 'ADD'
    add_x.inputs[1].default_value = x_R
    ng.links.new(rv_x.outputs[1], add_x.inputs[0])

    rv_y = ng.nodes.new('FunctionNodeRandomValue')
    rv_y.data_type = 'FLOAT'
    rv_y.inputs[2].default_value = -0.6
    rv_y.inputs[3].default_value = 0.6

    # NoiseTexture for Z
    noise = ng.nodes.new('ShaderNodeTexNoise')
    mr_z = ng.nodes.new('ShaderNodeMapRange')
    mr_z.inputs[3].default_value = -0.5
    mr_z.inputs[4].default_value = 0.5
    ng.links.new(noise.outputs[0], mr_z.inputs[0])    # Fac/Factor

    cxyz = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(add_x.outputs[0], cxyz.inputs[0])
    ng.links.new(rv_y.outputs[1], cxyz.inputs[1])
    ng.links.new(mr_z.outputs[0], cxyz.inputs[2])

    ng.links.new(cxyz.outputs[0], go.inputs[0])
    return ng

# --------------- params ---------------
def get_spider_params():
    params = {}
    params['num_leaf_versions'] = randint(4, 8)
    num_bases = randint(5, 12)
    params['num_plant_bases'] = num_bases
    base_radius, leaf_x_R, leaf_x_S = [], [], []
    init_base_radius = uniform(0.10, 0.20)
    diff_base_radius = init_base_radius - 0.04
    init_x_R, diff_x_R = uniform(1.2, 1.5), uniform(0.7, 1.1)
    init_x_S, diff_x_S = uniform(1.4, 2.0), uniform(0.2, 0.6)
    for i in range(num_bases):
        base_radius.append(init_base_radius - (i * diff_base_radius) / num_bases)
        leaf_x_R.append(init_x_R - (i * diff_x_R) / num_bases)
        leaf_x_S.append(init_x_S - (i * diff_x_S) / num_bases)
    params['base_radius'] = base_radius
    params['leaf_x_R'] = leaf_x_R
    params['leaf_x_S'] = leaf_x_S
    return params

# --------------- build main geometry ---------------
def build_spider_plant_ng(params):
    """Build the complete spider plant geometry nodes tree."""

    num_leaf_versions = params['num_leaf_versions']
    num_plant_bases = params['num_plant_bases']
    base_radius = params['base_radius']
    leaf_x_R = params['leaf_x_R']
    leaf_x_S = params['leaf_x_S']

    ng = bpy.data.node_groups.new('SpiderPlantGeometry', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput')

    # Build leaf geometry variants
    leaf_groups = []
    for v in range(num_leaf_versions):
        leaf_groups.append(build_leaf_geometry_ng(v))

    # Create leaf version nodes in main tree + GeometryToInstance
    leaf_nodes = []
    for lg in leaf_groups:
        grp = ng.nodes.new('GeometryNodeGroup')
        grp.node_tree = lg
        leaf_nodes.append(grp)

    g2i = ng.nodes.new('GeometryNodeGeometryToInstance')
    for ln in leaf_nodes:
        ng.links.new(ln.outputs[0], g2i.inputs[0])

    base_outputs = []

    for i in range(num_plant_bases):
        # CurveCircle for base
        cc = ng.nodes.new('GeometryNodeCurvePrimitiveCircle')
        cc.inputs[4].default_value = base_radius[i]           # Radius (index 4)

        # ResampleCurve
        rc = ng.nodes.new('GeometryNodeResampleCurve')
        ng.links.new(cc.outputs[0], rc.inputs[0])
        rc.inputs[3].default_value = randint(20, 40)           # Count (index 3)

        # Random XY offset for base points
        rv_x = ng.nodes.new('FunctionNodeRandomValue')
        rv_x.data_type = 'FLOAT'
        rv_x.inputs[2].default_value = -0.3 * base_radius[i]
        rv_x.inputs[3].default_value = 0.3 * base_radius[i]

        rv_y = ng.nodes.new('FunctionNodeRandomValue')
        rv_y.data_type = 'FLOAT'
        rv_y.inputs[2].default_value = -0.3 * base_radius[i]
        rv_y.inputs[3].default_value = 0.3 * base_radius[i]

        cxyz_off = ng.nodes.new('ShaderNodeCombineXYZ')
        ng.links.new(rv_x.outputs[1], cxyz_off.inputs[0])
        ng.links.new(rv_y.outputs[1], cxyz_off.inputs[1])

        sp_off = ng.nodes.new('GeometryNodeSetPosition')
        ng.links.new(rc.outputs[0], sp_off.inputs[0])
        ng.links.new(cxyz_off.outputs[0], sp_off.inputs[3])

        # SubdivisionSurface on instances (for geometry to instance output)
        subdiv = ng.nodes.new('GeometryNodeSubdivisionSurface')
        subdiv.inputs[1].default_value = 0
        ng.links.new(g2i.outputs[0], subdiv.inputs[0])

        # Leaf scale/align: normal alignment + noise scale
        inp_norm = ng.nodes.new('GeometryNodeInputNormal')
        align = ng.nodes.new('FunctionNodeAlignEulerToVector')
        align.axis = 'Y'
        ng.links.new(inp_norm.outputs[0], align.inputs[2])    # Vector

        noise_s = ng.nodes.new('ShaderNodeTexNoise')
        mr_s = ng.nodes.new('ShaderNodeMapRange')
        mr_s.inputs[3].default_value = 0.6
        mr_s.inputs[4].default_value = 1.1
        ng.links.new(noise_s.outputs[0], mr_s.inputs[0])

        # InstanceOnPoints
        iop = ng.nodes.new('GeometryNodeInstanceOnPoints')
        ng.links.new(sp_off.outputs[0], iop.inputs[0])        # Points
        ng.links.new(subdiv.outputs[0], iop.inputs[2])         # Instance
        iop.inputs[3].default_value = True                     # Pick Instance
        ng.links.new(align.outputs[0], iop.inputs[5])          # Rotation
        ng.links.new(mr_s.outputs[0], iop.inputs[6])           # Scale

        # ScaleInstances
        val_s = ng.nodes.new('ShaderNodeValue')
        val_s.outputs[0].default_value = leaf_x_S[i]

        si = ng.nodes.new('GeometryNodeScaleInstances')
        ng.links.new(iop.outputs[0], si.inputs[0])
        ng.links.new(val_s.outputs[0], si.inputs[2])           # Scale

        # RotateInstances with leaf_rotate_on_base
        rot_ng = build_leaf_rotate_on_base_ng(leaf_x_R[i])
        rot_grp = ng.nodes.new('GeometryNodeGroup')
        rot_grp.node_tree = rot_ng

        ri = ng.nodes.new('GeometryNodeRotateInstances')
        ng.links.new(si.outputs[0], ri.inputs[0])
        ng.links.new(rot_grp.outputs[0], ri.inputs[2])         # Rotation

        # RealizeInstances
        real = ng.nodes.new('GeometryNodeRealizeInstances')
        ng.links.new(ri.outputs[0], real.inputs[0])

        base_outputs.append(real)

    # Join all bases
    join = ng.nodes.new('GeometryNodeJoinGeometry')
    for bo in base_outputs:
        ng.links.new(bo.outputs[0], join.inputs[0])

    # SetShadeSmooth
    smooth = ng.nodes.new('GeometryNodeSetShadeSmooth')
    ng.links.new(join.outputs[0], smooth.inputs[0])

    ng.links.new(smooth.outputs[0], go.inputs[0])
    return ng

# --------------- make_spider_plant ---------------
def make_spider_plant():
    bpy.ops.mesh.primitive_plane_add(
        size=1, enter_editmode=False, align='WORLD',
        location=(0, 0, 0), scale=(1, 1, 1),
    )
    obj = bpy.context.active_object

    params = get_spider_params()
    tree = build_spider_plant_ng(params)

    mod = obj.modifiers.new('SpiderPlant', 'NODES')
    mod.node_group = tree

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

    obj.scale = (0.1, 0.1, 0.1)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # --- Material assignment (Phase 1 material, appended after geometry) ---
    obj.data.materials.clear()
    obj.data.materials.append(MAT_SPIDER_PLANT)

    return obj

make_spider_plant()
