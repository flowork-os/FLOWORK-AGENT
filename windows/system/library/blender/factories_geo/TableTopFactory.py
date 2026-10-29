# [FL_INDEX: keywords="blender_factory, procedural_3d, TableTopFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TableTopFactory | Category: factories_geo
# Prompt: A 3D model of an isolated tabletop surface rendered from an elevated three-quarter perspective, featuring a rounded-square (squircle) shape with smooth convex edges and a slight uniform thickness, presented without any legs or supporting structure.

import math
import random

import bpy

# ── seed handling ──────────────────────────────────────────────────────────────

SEED = 0
random.seed(SEED)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    bpy.context.scene.cursor.location = (0, 0, 0)

def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def new_link(tree, from_socket, to_socket):
    tree.links.new(from_socket, to_socket)

def set_fillet_mode(node, mode):
    """Handle Blender 5.0 FilletCurve mode change: property -> Menu socket."""

    try:
        node.mode = mode
    except AttributeError:
        pass
    # Blender 5.0: mode is a Menu input socket
    for inp in node.inputs:
        if inp.bl_idname == "NodeSocketMenu" or inp.name == "Mode":
            try:
                # mode values: "POLY" -> "Poly", "BEZIER" -> "Bezier"
                inp.default_value = mode.title()
            except Exception:
                pass
            break

def set_capture_data_type(node, dtype):
    """Configure CaptureAttribute data type for Blender 5.0+."""

    if hasattr(node, 'capture_items'):
        if len(node.capture_items) == 0:
            node.capture_items.new(dtype, 'Value')
        else:
            node.capture_items[0].data_type = dtype
    else:
        try:
            node.data_type = dtype
        except AttributeError:
            pass

def set_sample_curve_all(node):
    """Set use_all_curves on SampleCurve if available."""

    try:
        node.use_all_curves = True
    except AttributeError:
        pass


def build_n_gon_profile():
    """

    nodegroup_n_gon_profile: CurveCircle -> rotate -> scale -> FilletCurve
    Inputs: Profile N-gon(INT), Profile Width(FLOAT), Profile Aspect Ratio(FLOAT), Profile Fillet Ratio(FLOAT)
    Output: Curve
    """

    ng = bpy.data.node_groups.new("n_gon_profile", "GeometryNodeTree")
    # Interface
    ng.interface.new_socket("Profile N-gon", in_out="INPUT", socket_type="NodeSocketInt")
    ng.interface.new_socket("Profile Width", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Profile Aspect Ratio", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Profile Fillet Ratio", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Output", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    # Set defaults
    for item in ng.interface.items_tree:
        if hasattr(item, "default_value"):
            if item.name == "Profile N-gon":
                item.default_value = 4
            elif item.name == "Profile Width":
                item.default_value = 1.0
            elif item.name == "Profile Aspect Ratio":
                item.default_value = 1.0
            elif item.name == "Profile Fillet Ratio":
                item.default_value = 0.2

    nodes = {}
    n = nodes
    L = new_link

    n["in"] = ng.nodes.new("NodeGroupInput")
    n["out"] = ng.nodes.new("NodeGroupOutput")

    # Value 0.5
    n["val"] = ng.nodes.new("ShaderNodeValue")
    n["val"].outputs[0].default_value = 0.5

    # CurveCircle
    n["cc"] = ng.nodes.new("GeometryNodeCurvePrimitiveCircle")
    n["cc"].mode = "RADIUS"
    L(ng, n["in"].outputs["Profile N-gon"], n["cc"].inputs["Resolution"])
    L(ng, n["val"].outputs[0], n["cc"].inputs["Radius"])

    # divide = pi / N-gon
    n["div"] = ng.nodes.new("ShaderNodeMath")
    n["div"].operation = "DIVIDE"
    n["div"].inputs[0].default_value = math.pi
    L(ng, n["in"].outputs["Profile N-gon"], n["div"].inputs[1])

    # Rotate by pi/N around Z
    n["cz1"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["div"].outputs[0], n["cz1"].inputs["Z"])

    n["t1"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["cc"].outputs["Curve"], n["t1"].inputs["Geometry"])
    L(ng, n["cz1"].outputs[0], n["t1"].inputs["Rotation"])

    # Rotate -pi/2 around Z
    n["t2"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["t1"].outputs[0], n["t2"].inputs["Geometry"])
    n["t2"].inputs["Rotation"].default_value = (0, 0, -math.pi / 2)

    # Scale: X=Width, Y=Width*AspectRatio, Z=1
    n["mul_ar"] = ng.nodes.new("ShaderNodeMath")
    n["mul_ar"].operation = "MULTIPLY"
    L(ng, n["in"].outputs["Profile Aspect Ratio"], n["mul_ar"].inputs[0])
    L(ng, n["in"].outputs["Profile Width"], n["mul_ar"].inputs[1])

    n["cxyz"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["in"].outputs["Profile Width"], n["cxyz"].inputs["X"])
    L(ng, n["mul_ar"].outputs[0], n["cxyz"].inputs["Y"])
    n["cxyz"].inputs["Z"].default_value = 1.0

    n["t3"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["t2"].outputs[0], n["t3"].inputs["Geometry"])
    L(ng, n["cxyz"].outputs[0], n["t3"].inputs["Scale"])

    # Fillet = Width * FilletRatio
    n["mul_f"] = ng.nodes.new("ShaderNodeMath")
    n["mul_f"].operation = "MULTIPLY"
    L(ng, n["in"].outputs["Profile Width"], n["mul_f"].inputs[0])
    L(ng, n["in"].outputs["Profile Fillet Ratio"], n["mul_f"].inputs[1])

    # FilletCurve
    n["fc"] = ng.nodes.new("GeometryNodeFilletCurve")
    set_fillet_mode(n["fc"], "POLY")
    L(ng, n["t3"].outputs[0], n["fc"].inputs["Curve"])
    n["fc"].inputs["Count"].default_value = 8
    L(ng, n["mul_f"].outputs[0], n["fc"].inputs["Radius"])
    n["fc"].inputs["Limit Radius"].default_value = True

    L(ng, n["fc"].outputs[0], n["out"].inputs["Output"])

    return ng

def build_n_gon_cylinder():
    """

    nodegroup_n_gon_cylinder: sweep n_gon_profile along a line, deform by radius curve.
    Inputs: Radius Curve(GEO), Height(FLOAT), N-gon(INT), Profile Width(FLOAT),
            Aspect Ratio(FLOAT), Fillet Ratio(FLOAT), Profile Resolution(INT), Resolution(INT)
    Outputs: Mesh(GEO), Profile Curve(GEO), Caps(GEO)
    """

    ng = bpy.data.node_groups.new("n_gon_cylinder", "GeometryNodeTree")
    ng.interface.new_socket("Radius Curve", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Height", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("N-gon", in_out="INPUT", socket_type="NodeSocketInt")
    ng.interface.new_socket("Profile Width", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Aspect Ratio", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Fillet Ratio", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Profile Resolution", in_out="INPUT", socket_type="NodeSocketInt")
    ng.interface.new_socket("Resolution", in_out="INPUT", socket_type="NodeSocketInt")
    ng.interface.new_socket("Mesh", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Profile Curve", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Caps", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    # Set defaults
    for item in ng.interface.items_tree:
        if hasattr(item, "default_value"):
            if item.name == "Height":
                item.default_value = 0.5
            elif item.name == "Profile Width":
                item.default_value = 0.5
            elif item.name == "Aspect Ratio":
                item.default_value = 0.5
            elif item.name == "Fillet Ratio":
                item.default_value = 0.2
            elif item.name == "Profile Resolution":
                item.default_value = 64
            elif item.name == "Resolution":
                item.default_value = 128

    n = {}
    L = new_link

    n["in"] = ng.nodes.new("NodeGroupInput")
    n["out"] = ng.nodes.new("NodeGroupOutput")

    # multiply height by -1
    n["mul_h"] = ng.nodes.new("ShaderNodeMath")
    n["mul_h"].operation = "MULTIPLY"
    L(ng, n["in"].outputs["Height"], n["mul_h"].inputs[0])
    n["mul_h"].inputs[1].default_value = -1.0

    # CombineXYZ -> Z = -Height
    n["cz_h"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["mul_h"].outputs[0], n["cz_h"].inputs["Z"])

    # CurveLine from (0,0,0) to (0,0,-Height)
    n["cl"] = ng.nodes.new("GeometryNodeCurvePrimitiveLine")
    L(ng, n["cz_h"].outputs[0], n["cl"].inputs["End"])

    # SetCurveTilt = pi
    n["tilt"] = ng.nodes.new("GeometryNodeSetCurveTilt")
    L(ng, n["cl"].outputs[0], n["tilt"].inputs["Curve"])
    n["tilt"].inputs["Tilt"].default_value = math.pi

    # ResampleCurve
    n["rs"] = ng.nodes.new("GeometryNodeResampleCurve")
    L(ng, n["tilt"].outputs[0], n["rs"].inputs["Curve"])
    L(ng, n["in"].outputs["Resolution"], n["rs"].inputs["Count"])

    # SplineParameter
    n["sp"] = ng.nodes.new("GeometryNodeSplineParameter")

    # CaptureAttribute
    n["cap"] = ng.nodes.new("GeometryNodeCaptureAttribute")
    set_capture_data_type(n["cap"], "FLOAT")
    L(ng, n["rs"].outputs[0], n["cap"].inputs["Geometry"])
    # Connect Factor to the capture value input
    # In Blender 5.0 with capture_items, the value input is at index 1
    val_input = None
    for i, inp in enumerate(n["cap"].inputs):
        if inp.name == "Value" and inp.bl_idname != "NodeSocketGeometry":
            val_input = inp
            break
    if val_input is None:
        val_input = n["cap"].inputs[1]
    L(ng, n["sp"].outputs["Factor"], val_input)

    # n_gon_profile group
    n["ngp"] = ng.nodes.new("GeometryNodeGroup")
    n["ngp"].node_tree = bpy.data.node_groups["n_gon_profile"]
    L(ng, n["in"].outputs["N-gon"], n["ngp"].inputs["Profile N-gon"])
    L(ng, n["in"].outputs["Profile Width"], n["ngp"].inputs["Profile Width"])
    L(ng, n["in"].outputs["Aspect Ratio"], n["ngp"].inputs["Profile Aspect Ratio"])
    L(ng, n["in"].outputs["Fillet Ratio"], n["ngp"].inputs["Profile Fillet Ratio"])

    # ResampleCurve for profile
    n["rs2"] = ng.nodes.new("GeometryNodeResampleCurve")
    L(ng, n["ngp"].outputs[0], n["rs2"].inputs["Curve"])
    L(ng, n["in"].outputs["Profile Resolution"], n["rs2"].inputs["Count"])

    # CurveToMesh
    n["c2m"] = ng.nodes.new("GeometryNodeCurveToMesh")
    # Find captured geometry output
    cap_geo_out = n["cap"].outputs["Geometry"] if "Geometry" in n["cap"].outputs else n["cap"].outputs[0]
    L(ng, cap_geo_out, n["c2m"].inputs["Curve"])
    L(ng, n["rs2"].outputs[0], n["c2m"].inputs["Profile Curve"])
    n["c2m"].inputs["Fill Caps"].default_value = True

    # Get captured attribute output
    cap_attr_out = None
    for o in n["cap"].outputs:
        if o.name == "Value" and o.bl_idname != "NodeSocketGeometry":
            cap_attr_out = o
            break
    if cap_attr_out is None:
        cap_attr_out = n["cap"].outputs[1]

    # Position -> SeparateXYZ (for mesh positions)
    n["pos1"] = ng.nodes.new("GeometryNodeInputPosition")
    n["sep1"] = ng.nodes.new("ShaderNodeSeparateXYZ")
    L(ng, n["pos1"].outputs[0], n["sep1"].inputs[0])

    # SampleCurve on Radius Curve
    n["sc"] = ng.nodes.new("GeometryNodeSampleCurve")
    set_sample_curve_all(n["sc"])
    L(ng, n["in"].outputs["Radius Curve"], n["sc"].inputs["Curves"])
    L(ng, cap_attr_out, n["sc"].inputs["Factor"])

    # SeparateXYZ on sampled position
    n["sep2"] = ng.nodes.new("ShaderNodeSeparateXYZ")
    L(ng, n["sc"].outputs["Position"], n["sep2"].inputs[0])

    # CombineXYZ(X, Y, 0) -> Length
    n["cxy"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["sep2"].outputs["X"], n["cxy"].inputs["X"])
    L(ng, n["sep2"].outputs["Y"], n["cxy"].inputs["Y"])

    n["len"] = ng.nodes.new("ShaderNodeVectorMath")
    n["len"].operation = "LENGTH"
    L(ng, n["cxy"].outputs[0], n["len"].inputs[0])

    # Multiply mesh X,Y by length
    n["mulx"] = ng.nodes.new("ShaderNodeMath")
    n["mulx"].operation = "MULTIPLY"
    L(ng, n["sep1"].outputs["X"], n["mulx"].inputs[0])
    L(ng, n["len"].outputs["Value"], n["mulx"].inputs[1])

    n["muly"] = ng.nodes.new("ShaderNodeMath")
    n["muly"].operation = "MULTIPLY"
    L(ng, n["sep1"].outputs["Y"], n["muly"].inputs[0])
    L(ng, n["len"].outputs["Value"], n["muly"].inputs[1])

    # AttributeStatistic on radius curve Z
    n["pos2"] = ng.nodes.new("GeometryNodeInputPosition")
    n["sep3"] = ng.nodes.new("ShaderNodeSeparateXYZ")
    L(ng, n["pos2"].outputs[0], n["sep3"].inputs[0])

    n["as"] = ng.nodes.new("GeometryNodeAttributeStatistic")
    n["as"].data_type = "FLOAT"
    L(ng, n["in"].outputs["Radius Curve"], n["as"].inputs["Geometry"])
    # Attribute input - find FLOAT input
    as_attr_input = None
    for inp in n["as"].inputs:
        if inp.name == "Attribute" and inp.bl_idname == "NodeSocketFloat":
            as_attr_input = inp
            break
    if as_attr_input is None:
        as_attr_input = n["as"].inputs[2]
    L(ng, n["sep3"].outputs["Z"], as_attr_input)

    # MapRange: sampled Z -> [-Height, 0]
    n["mr"] = ng.nodes.new("ShaderNodeMapRange")
    L(ng, n["sep2"].outputs["Z"], n["mr"].inputs["Value"])
    L(ng, n["as"].outputs["Min"], n["mr"].inputs[1])  # From Min
    L(ng, n["as"].outputs["Max"], n["mr"].inputs[2])  # From Max
    L(ng, n["mul_h"].outputs[0], n["mr"].inputs[3])   # To Min = -Height
    n["mr"].inputs[4].default_value = 0.0              # To Max

    # CombineXYZ(mulx, muly, maprange)
    n["cfinal"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["mulx"].outputs[0], n["cfinal"].inputs["X"])
    L(ng, n["muly"].outputs[0], n["cfinal"].inputs["Y"])
    L(ng, n["mr"].outputs["Result"], n["cfinal"].inputs["Z"])

    # SetPosition
    n["sp2"] = ng.nodes.new("GeometryNodeSetPosition")
    L(ng, n["c2m"].outputs[0], n["sp2"].inputs["Geometry"])
    L(ng, n["cfinal"].outputs[0], n["sp2"].inputs["Position"])

    # Caps: delete all but last 2 faces from curve_to_mesh
    n["idx"] = ng.nodes.new("GeometryNodeInputIndex")
    n["ds"] = ng.nodes.new("GeometryNodeAttributeDomainSize")
    L(ng, n["c2m"].outputs[0], n["ds"].inputs[0])

    n["sub"] = ng.nodes.new("ShaderNodeMath")
    n["sub"].operation = "SUBTRACT"
    L(ng, n["ds"].outputs["Face Count"], n["sub"].inputs[0])
    n["sub"].inputs[1].default_value = 2.0

    n["lt"] = ng.nodes.new("FunctionNodeCompare")
    n["lt"].data_type = "INT"
    n["lt"].operation = "LESS_THAN"
    L(ng, n["idx"].outputs[0], n["lt"].inputs[2])
    L(ng, n["sub"].outputs[0], n["lt"].inputs[3])

    n["del"] = ng.nodes.new("GeometryNodeDeleteGeometry")
    n["del"].domain = "FACE"
    L(ng, n["c2m"].outputs[0], n["del"].inputs["Geometry"])
    L(ng, n["lt"].outputs[0], n["del"].inputs["Selection"])

    # Outputs
    L(ng, n["sp2"].outputs[0], n["out"].inputs["Mesh"])
    L(ng, n["rs2"].outputs[0], n["out"].inputs["Profile Curve"])
    L(ng, n["del"].outputs[0], n["out"].inputs["Caps"])

    return ng

def build_create_cap():
    """

    nodegroup_create_cap: UV sphere cut in half, shifted down.
    Inputs: Radius(FLOAT), Resolution(INT)
    Output: Mesh
    """

    ng = bpy.data.node_groups.new("create_cap", "GeometryNodeTree")
    ng.interface.new_socket("Radius", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Resolution", in_out="INPUT", socket_type="NodeSocketInt")
    ng.interface.new_socket("Mesh", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    for item in ng.interface.items_tree:
        if hasattr(item, "default_value"):
            if item.name == "Radius":
                item.default_value = 1.0
            elif item.name == "Resolution":
                item.default_value = 64

    n = {}
    L = new_link

    n["in"] = ng.nodes.new("NodeGroupInput")
    n["out"] = ng.nodes.new("NodeGroupOutput")

    # Rings = Radius * 257
    n["mul"] = ng.nodes.new("ShaderNodeMath")
    n["mul"].operation = "MULTIPLY"
    L(ng, n["in"].outputs["Radius"], n["mul"].inputs[0])
    n["mul"].inputs[1].default_value = 257.0

    # UV Sphere
    n["uv"] = ng.nodes.new("GeometryNodeMeshUVSphere")
    L(ng, n["in"].outputs["Resolution"], n["uv"].inputs["Segments"])
    L(ng, n["mul"].outputs[0], n["uv"].inputs["Rings"])
    L(ng, n["in"].outputs["Radius"], n["uv"].inputs["Radius"])

    # StoreNamedAttribute for UV (optional, skip for mesh-only)
    # Just pass through since we don't need UVs

    # Translation: Z = -sqrt(Radius^2 - 1)
    n["pow"] = ng.nodes.new("ShaderNodeMath")
    n["pow"].operation = "POWER"
    L(ng, n["in"].outputs["Radius"], n["pow"].inputs[0])
    n["pow"].inputs[1].default_value = 2.0

    n["sub"] = ng.nodes.new("ShaderNodeMath")
    n["sub"].operation = "SUBTRACT"
    L(ng, n["pow"].outputs[0], n["sub"].inputs[0])
    n["sub"].inputs[1].default_value = 1.0

    n["sqrt"] = ng.nodes.new("ShaderNodeMath")
    n["sqrt"].operation = "SQRT"
    L(ng, n["sub"].outputs[0], n["sqrt"].inputs[0])

    n["neg"] = ng.nodes.new("ShaderNodeMath")
    n["neg"].operation = "MULTIPLY"
    L(ng, n["sqrt"].outputs[0], n["neg"].inputs[0])
    n["neg"].inputs[1].default_value = -1.0

    n["cz"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["neg"].outputs[0], n["cz"].inputs["Z"])

    n["tf"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["uv"].outputs["Mesh"], n["tf"].inputs["Geometry"])
    L(ng, n["cz"].outputs[0], n["tf"].inputs["Translation"])

    # Delete below Z=0
    n["pos"] = ng.nodes.new("GeometryNodeInputPosition")
    n["sep"] = ng.nodes.new("ShaderNodeSeparateXYZ")
    L(ng, n["pos"].outputs[0], n["sep"].inputs[0])

    n["lt"] = ng.nodes.new("FunctionNodeCompare")
    n["lt"].operation = "LESS_THAN"
    L(ng, n["sep"].outputs["Z"], n["lt"].inputs[0])

    n["del"] = ng.nodes.new("GeometryNodeDeleteGeometry")
    L(ng, n["tf"].outputs[0], n["del"].inputs["Geometry"])
    L(ng, n["lt"].outputs[0], n["del"].inputs["Selection"])

    L(ng, n["del"].outputs[0], n["out"].inputs["Mesh"])

    return ng

def build_generate_table_top():
    """

    nodegroup_generate_table_top: creates the table top slab.
    Uses n_gon_cylinder to sweep an n-gon profile along a vertical line,
    then adds vertical fillet edge profile via CurveToMesh.
    Inputs: Thickness, N-gon, Profile Width, Aspect Ratio, Fillet Ratio, Fillet Radius Vertical
    Outputs: Geometry, Curve (profile curve)
    """

    ng = bpy.data.node_groups.new("generate_table_top", "GeometryNodeTree")
    ng.interface.new_socket("Thickness", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("N-gon", in_out="INPUT", socket_type="NodeSocketInt")
    ng.interface.new_socket("Profile Width", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Aspect Ratio", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Fillet Ratio", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Fillet Radius Vertical", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Curve", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    for item in ng.interface.items_tree:
        if hasattr(item, "default_value"):
            if item.name == "Thickness":
                item.default_value = 0.5
            elif item.name == "Profile Width":
                item.default_value = 0.5
            elif item.name == "Aspect Ratio":
                item.default_value = 0.5
            elif item.name == "Fillet Ratio":
                item.default_value = 0.2

    n = {}
    L = new_link

    n["in"] = ng.nodes.new("NodeGroupInput")
    n["out"] = ng.nodes.new("NodeGroupOutput")

    # CurveLine from (1,0,1) to (1,0,-1) - straight radius curve
    n["cl"] = ng.nodes.new("GeometryNodeCurvePrimitiveLine")
    n["cl"].inputs["Start"].default_value = (1.0, 0.0, 1.0)
    n["cl"].inputs["End"].default_value = (1.0, 0.0, -1.0)

    # n_gon_cylinder
    n["ngc"] = ng.nodes.new("GeometryNodeGroup")
    n["ngc"].node_tree = bpy.data.node_groups["n_gon_cylinder"]
    L(ng, n["cl"].outputs[0], n["ngc"].inputs["Radius Curve"])
    L(ng, n["in"].outputs["Thickness"], n["ngc"].inputs["Height"])
    L(ng, n["in"].outputs["N-gon"], n["ngc"].inputs["N-gon"])
    L(ng, n["in"].outputs["Profile Width"], n["ngc"].inputs["Profile Width"])
    L(ng, n["in"].outputs["Aspect Ratio"], n["ngc"].inputs["Aspect Ratio"])
    L(ng, n["in"].outputs["Fillet Ratio"], n["ngc"].inputs["Fillet Ratio"])
    n["ngc"].inputs["Profile Resolution"].default_value = 512
    n["ngc"].inputs["Resolution"].default_value = 10

    # Vertical fillet: Arc curve for edge profile
    # Arc(res=4, radius=0.7071, sweep=4.7124=270deg)
    n["arc"] = ng.nodes.new("GeometryNodeCurveArc")
    n["arc"].inputs["Resolution"].default_value = 4
    n["arc"].inputs["Radius"].default_value = 0.7071
    n["arc"].inputs["Sweep Angle"].default_value = 4.7124

    # Rotate arc by -45deg around Z
    n["t1"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["arc"].outputs["Curve"], n["t1"].inputs["Geometry"])
    n["t1"].inputs["Rotation"].default_value = (0, 0, -0.7854)

    # Rotate 90deg around Y
    n["t2"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["t1"].outputs[0], n["t2"].inputs["Geometry"])
    n["t2"].inputs["Rotation"].default_value = (0, math.pi / 2, 0)

    # Translate Y=0.5
    n["t3"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["t2"].outputs[0], n["t3"].inputs["Geometry"])
    n["t3"].inputs["Translation"].default_value = (0, 0.5, 0)

    # Scale: X=1, Y=Fillet Radius Vertical, Z=1
    n["cxyz_fr"] = ng.nodes.new("ShaderNodeCombineXYZ")
    n["cxyz_fr"].inputs["X"].default_value = 1.0
    L(ng, n["in"].outputs["Fillet Radius Vertical"], n["cxyz_fr"].inputs["Y"])
    n["cxyz_fr"].inputs["Z"].default_value = 1.0

    n["t4"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["t3"].outputs[0], n["t4"].inputs["Geometry"])
    L(ng, n["cxyz_fr"].outputs[0], n["t4"].inputs["Scale"])

    # FilletCurve POLY
    n["fc"] = ng.nodes.new("GeometryNodeFilletCurve")
    set_fillet_mode(n["fc"], "POLY")
    L(ng, n["t4"].outputs[0], n["fc"].inputs["Curve"])
    n["fc"].inputs["Count"].default_value = 8
    L(ng, n["in"].outputs["Fillet Radius Vertical"], n["fc"].inputs["Radius"])
    n["fc"].inputs["Limit Radius"].default_value = True

    # Scale+rotate the fillet curve: rotation=(pi/2, pi/2, 0), scale=Thickness
    n["t5"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["fc"].outputs[0], n["t5"].inputs["Geometry"])
    n["t5"].inputs["Rotation"].default_value = (math.pi / 2, math.pi / 2, 0)
    L(ng, n["in"].outputs["Thickness"], n["t5"].inputs["Scale"])

    # CurveToMesh: profile curve + vertical fillet edge
    n["c2m"] = ng.nodes.new("GeometryNodeCurveToMesh")
    L(ng, n["ngc"].outputs["Profile Curve"], n["c2m"].inputs["Curve"])
    L(ng, n["t5"].outputs[0], n["c2m"].inputs["Profile Curve"])

    # Translate edge mesh down by Thickness*-0.5
    n["mul_th"] = ng.nodes.new("ShaderNodeMath")
    n["mul_th"].operation = "MULTIPLY"
    L(ng, n["in"].outputs["Thickness"], n["mul_th"].inputs[0])
    n["mul_th"].inputs[1].default_value = -0.5

    n["cz_th"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["mul_th"].outputs[0], n["cz_th"].inputs["Z"])

    n["t6"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["c2m"].outputs[0], n["t6"].inputs["Geometry"])
    L(ng, n["cz_th"].outputs[0], n["t6"].inputs["Translation"])

    # Get caps from n_gon_cylinder (top cap only - index==0)
    n["idx"] = ng.nodes.new("GeometryNodeInputIndex")
    n["eq"] = ng.nodes.new("FunctionNodeCompare")
    n["eq"].data_type = "INT"
    n["eq"].operation = "EQUAL"
    L(ng, n["idx"].outputs[0], n["eq"].inputs[2])
    n["eq"].inputs[3].default_value = 0

    # We skip the tag_nodegroup, just use caps directly
    # Join edge mesh + caps
    n["join"] = ng.nodes.new("GeometryNodeJoinGeometry")
    L(ng, n["t6"].outputs[0], n["join"].inputs["Geometry"])
    L(ng, n["ngc"].outputs["Caps"], n["join"].inputs["Geometry"])

    # FlipFaces
    n["flip"] = ng.nodes.new("GeometryNodeFlipFaces")
    L(ng, n["join"].outputs[0], n["flip"].inputs["Mesh"])

    # Translate up by Thickness
    n["cz_up"] = ng.nodes.new("ShaderNodeCombineXYZ")
    L(ng, n["in"].outputs["Thickness"], n["cz_up"].inputs["Z"])

    n["t7"] = ng.nodes.new("GeometryNodeTransform")
    L(ng, n["flip"].outputs[0], n["t7"].inputs["Geometry"])
    L(ng, n["cz_up"].outputs[0], n["t7"].inputs["Translation"])

    # Outputs
    L(ng, n["t7"].outputs[0], n["out"].inputs["Geometry"])
    L(ng, n["ngc"].outputs["Profile Curve"], n["out"].inputs["Curve"])

    return ng

# ── main ───────────────────────────────────────────────────────────────────────

def sample_parameters():
    return {
        "Profile N-gon": 4,
        "Profile Width": 1.0,
        "Profile Aspect Ratio": 1.0,
        "Profile Fillet Ratio": 0.2,
        "Thickness": 0.1,
        "Vertical Fillet Ratio": 0.2,
    }

def create_table_top(params):
    # Build nodegroups
    build_n_gon_profile()
    build_n_gon_cylinder()
    build_create_cap()
    build_generate_table_top()

    # Create base mesh
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "TableTopFactory"

    # Build wrapper nodegroup
    ng = bpy.data.node_groups.new("table_top_wrapper", "GeometryNodeTree")
    geo_in = ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    n_in = ng.nodes.new("NodeGroupInput")
    n_out = ng.nodes.new("NodeGroupOutput")

    # generate_table_top node
    n_gtt = ng.nodes.new("GeometryNodeGroup")
    n_gtt.node_tree = bpy.data.node_groups["generate_table_top"]
    n_gtt.inputs["Thickness"].default_value = params["Thickness"]
    n_gtt.inputs["N-gon"].default_value = params["Profile N-gon"]
    n_gtt.inputs["Profile Width"].default_value = params["Profile Width"]
    n_gtt.inputs["Aspect Ratio"].default_value = params["Profile Aspect Ratio"]
    n_gtt.inputs["Fillet Ratio"].default_value = params["Profile Fillet Ratio"]
    n_gtt.inputs["Fillet Radius Vertical"].default_value = params["Vertical Fillet Ratio"]

    ng.links.new(n_gtt.outputs["Geometry"], n_out.inputs["Geometry"])

    # Add modifier
    mod = obj.modifiers.new("GeometryNodes", "NODES")
    mod.node_group = ng

    # Apply modifier
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    return obj

def main():
    clear_scene()
    params = sample_parameters()
    obj = create_table_top(params)

if __name__ == "__main__":
    main()
