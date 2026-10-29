# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, all_in_one_printer_with_scanner_lid_and_paper_tray, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: all_in_one_printer_with_scanner_lid_and_paper_tray

from __future__ import annotations

import cadquery as cq
import math

# ===== shim core =====
def _rpy_R(r, p, y):
    """Rotation matrix Rz(yaw)@Ry(pitch)@Rx(roll) as rows (URDF convention)."""
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    return (
        (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
        (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
        (-sp,     cp * sr,                cp * cr),
    )

def _mat_mul(A, B):
    return tuple(
        tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )

def _mat_vec(A, v):
    return tuple(sum(A[i][k] * v[k] for k in range(3)) for i in range(3))

class _Tf:
    """Rigid transform: rotation matrix R (rows) + translation t."""
    __slots__ = ("R", "t")
    _I = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

    def __init__(self, R=None, t=(0.0, 0.0, 0.0)):
        self.R = R if R is not None else _Tf._I
        self.t = (float(t[0]), float(t[1]), float(t[2]))

    @staticmethod
    def from_origin(origin):
        if origin is None:
            return _Tf()
        xyz = getattr(origin, "xyz", (0.0, 0.0, 0.0))
        rpy = getattr(origin, "rpy", (0.0, 0.0, 0.0))
        return _Tf(_rpy_R(rpy[0], rpy[1], rpy[2]), xyz)

    def __matmul__(self, o):
        return _Tf(_mat_mul(self.R, o.R),
                   tuple(a + b for a, b in zip(_mat_vec(self.R, o.t), self.t)))

    def location(self):
        R, t = self.R, self.t
        xdir = cq.Vector(R[0][0], R[1][0], R[2][0])
        zdir = cq.Vector(R[0][2], R[1][2], R[2][2])
        return cq.Location(cq.Plane(origin=cq.Vector(*t), xDir=xdir, normal=zdir))

class ValidationError(ValueError):
    pass

class ArticulationType:
    REVOLUTE = "revolute"
    CONTINUOUS = "continuous"
    PRISMATIC = "prismatic"
    FIXED = "fixed"
    FLOATING = "floating"

class Origin:
    __slots__ = ("xyz", "rpy")

    def __init__(self, xyz=(0.0, 0.0, 0.0), rpy=(0.0, 0.0, 0.0)):
        self.xyz = (float(xyz[0]), float(xyz[1]), float(xyz[2]))
        self.rpy = (float(rpy[0]), float(rpy[1]), float(rpy[2]))

class Material:
    def __init__(self, name, rgba=None, texture=None, *, color=None):
        self.name = str(name)
        c = rgba if rgba is not None else color
        if c is not None:
            c = tuple(float(v) for v in c)
            if len(c) == 3:
                c = c + (1.0,)
        self.rgba = c
        self.texture = texture

class MotionLimits:
    def __init__(self, effort=1.0, velocity=1.0, lower=None, upper=None):
        self.effort = float(effort)
        self.velocity = float(velocity)
        self.lower = None if lower is None else float(lower)
        self.upper = None if upper is None else float(upper)

class Box:
    __slots__ = ("size",)

    def __init__(self, size):
        self.size = (float(size[0]), float(size[1]), float(size[2]))

    def _cq(self):
        sx, sy, sz = self.size
        return cq.Solid.makeBox(sx, sy, sz, cq.Vector(-sx / 2, -sy / 2, -sz / 2))

def _to_shape(model):
    """Coerce a cadquery object (Workplane/Shape/Assembly) or a shim geometry
    wrapper into a single cq.Shape."""
    if isinstance(model, _CQMesh):
        return model.shape
    if hasattr(model, "_cq"):
        return model._cq()
    if isinstance(model, cq.Assembly):
        return model.toCompound()
    if isinstance(model, cq.Workplane):
        vals = [v for v in model.vals() if isinstance(v, cq.Shape)]
        if not vals:
            raise ValidationError("cadquery Workplane has no shape values")
        return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    if isinstance(model, cq.Shape):
        return model
    raise ValidationError("unsupported cadquery model type: %r" % type(model))

class _CQMesh:
    """Mesh stand-in that simply carries an exact cadquery B-rep shape."""
    __slots__ = ("shape", "name")

    def __init__(self, shape, name=None):
        self.shape = shape
        self.name = name

    def _cq(self):
        return self.shape

def mesh_from_cadquery(model, name=None, **kwargs):
    return _CQMesh(_to_shape(model), name=name if isinstance(name, str) else None)

class Visual:
    __slots__ = ("geometry", "origin", "material", "name")

    def __init__(self, geometry, origin=None, material=None, name=None):
        self.geometry = geometry
        self.origin = origin or Origin()
        self.material = material
        self.name = name

class Part:
    def __init__(self, name, visuals=None, inertial=None, meta=None):
        self.name = name
        self.visuals = list(visuals or [])
        self.collisions = []
        self.inertial = inertial
        self.meta = dict(meta or {})

    def visual(self, geometry, *, origin=None, material=None, color=None, name=None):
        if color is not None and material is None:
            material = color if isinstance(color, (str, Material)) else Material("inline", rgba=color)
        v = Visual(geometry, origin=origin, material=material, name=name)
        self.visuals.append(v)
        return v

    def get_visual(self, name):
        for v in self.visuals:
            if v.name == name:
                return v
        raise ValidationError("unknown visual %r" % name)

class Articulation:
    def __init__(self, name, articulation_type, parent, child, origin=None,
                 axis=(0.0, 0.0, 1.0), motion_limits=None, motion_properties=None,
                 mimic=None, meta=None):
        self.name = name
        self.articulation_type = articulation_type
        self.parent = parent if isinstance(parent, str) else parent.name
        self.child = child if isinstance(child, str) else child.name
        self.origin = origin or Origin()
        self.axis = tuple(float(a) for a in axis)
        self.motion_limits = motion_limits
        self.motion_properties = motion_properties
        self.mimic = mimic
        self.meta = dict(meta or {})

    # aliases used by some scripts
    @property
    def joint_type(self):
        return self.articulation_type

    @property
    def limit(self):
        return self.motion_limits

class ArticulatedObject:
    def __init__(self, name, parts=None, articulations=None, materials=None, meta=None, assets=None):
        self.name = name
        self.parts = list(parts or [])
        self.articulations = list(articulations or [])
        self.materials = list(materials or [])
        self.meta = dict(meta or {})
        self.assets = assets

    # ---- builders ----
    def part(self, name, *, visuals=None, inertial=None, meta=None):
        p = Part(name, visuals=visuals, inertial=inertial, meta=meta)
        self.parts.append(p)
        return p

    link = part

    def articulation(self, name, articulation_type, parent, child, *, origin=None,
                     axis=None, motion_limits=None, motion_properties=None, mimic=None, meta=None):
        a = Articulation(name, articulation_type, parent, child, origin=origin,
                         axis=axis or (0.0, 0.0, 1.0), motion_limits=motion_limits,
                         motion_properties=motion_properties, mimic=mimic, meta=meta)
        self.articulations.append(a)
        return a

    def joint(self, name, joint_type, parent, child, *, origin=None, axis=None,
              limit=None, dynamics=None, mimic=None, meta=None):
        return self.articulation(name, joint_type, parent, child, origin=origin, axis=axis,
                                 motion_limits=limit, motion_properties=dynamics, mimic=mimic, meta=meta)

    def material(self, name, *, rgba=None, color=None, texture=None):
        m = Material(name, rgba=rgba, color=color, texture=texture)
        self.materials.append(m)
        return m

    def set_assets(self, assets):
        self.assets = assets
        return assets

    # ---- queries ----
    def get_part(self, name):
        key = name if isinstance(name, str) else name.name
        for p in self.parts:
            if p.name == key:
                return p
        raise ValidationError("unknown part %r" % name)

    get_link = get_part

    def get_articulation(self, name):
        key = name if isinstance(name, str) else getattr(name, "name", name)
        for a in self.articulations:
            if a.name == key:
                return a
        raise ValidationError("unknown articulation %r" % name)

    get_joint = get_articulation

    def root_parts(self):
        children = {a.child for a in self.articulations}
        return [p for p in self.parts if p.name not in children]

    root_links = root_parts

    def validate(self, *a, **k):
        return None

    def to_urdf(self, *a, **k):
        raise ValidationError("URDF export is not available in self-contained CadQuery mode")

    # ---- rest-pose world transform per part (URDF forward kinematics, q=0) ----
    def _world_transforms(self):
        parent_of, joint_tf = {}, {}
        for a in self.articulations:
            parent_of[a.child] = a.parent
            joint_tf[a.child] = _Tf.from_origin(a.origin)
        cache = {}

        def world(name):
            if name in cache:
                return cache[name]
            if name in parent_of:
                tf = world(parent_of[name]) @ joint_tf[name]
            else:
                tf = _Tf()
            cache[name] = tf
            return tf

        return {p.name: world(p.name) for p in self.parts}

    # ---- assemble to a CadQuery Assembly in rest pose ----
    def to_cq(self):
        worlds = self._world_transforms()
        asm = cq.Assembly(name=self.name or "model")
        idx = 0
        for part in self.parts:
            wt = worlds.get(part.name, _Tf())
            for vis in part.visuals:
                try:
                    shape = _to_shape(vis.geometry)
                except Exception as exc:
                    raise ValidationError(
                        "part %r visual %r: %s" % (part.name, vis.name, exc)
                    )
                loc = (wt @ _Tf.from_origin(vis.origin)).location()
                rgba = None
                mat = vis.material
                if isinstance(mat, str):
                    mat = next((m for m in self.materials if m.name == mat), None)
                if isinstance(mat, Material) and mat.rgba:
                    rgba = mat.rgba
                kw = {"name": "%s_%d" % (part.name, idx)}
                if rgba:
                    kw["color"] = cq.Color(*rgba)
                asm.add(shape, loc=loc, **kw)
                idx += 1
        return asm

    # convenience aliases a few scripts might call
    def to_assembly(self):
        return self.to_cq()

    def compound(self):
        return self.to_cq().toCompound()

# ===== model =====
import math
import cadquery as cq
BODY_W = 0.445
BODY_D = 0.345
BODY_H = 0.102
CONTROL_STRIP_W = 0.240
CONTROL_STRIP_D = 0.046
CONTROL_STRIP_H = 0.008
CONTROL_Y = -BODY_D / 2.0 + 0.020 + CONTROL_STRIP_D / 2.0
CONTROL_TOP_Z = BODY_H + CONTROL_STRIP_H
SCANNER_OPENING_W = 0.330
SCANNER_OPENING_D = 0.225
SCANNER_RECESS = 0.008
SCANNER_CENTER_Y = 0.002
GLASS_W = 0.304
GLASS_D = 0.202
GLASS_T = 0.0025
LID_W = 0.392
LID_D = 0.224
LID_T = 0.016
LID_HINGE_Y = 0.124
LID_HINGE_Z = BODY_H + 0.0012
GUIDE_W = 0.312
GUIDE_D = 0.094
GUIDE_T = 0.0035
GUIDE_HINGE_Y = BODY_D / 2.0
GUIDE_HINGE_Z = BODY_H
TRAY_W = 0.308
TRAY_D = 0.050
TRAY_T = 0.0028
TRAY_WALL = 0.004
TRAY_LIP = 0.010
TRAY_HINGE_Z = 0.078
DIAL_R = 0.017
DIAL_H = 0.015
DIAL_X = -0.078
BUTTON_W = 0.017
BUTTON_D = 0.011
BUTTON_H = 0.0034
BUTTON_TRAVEL = 0.0018
BUTTON_XS = (-0.020, 0.008, 0.036, 0.064)
BUTTON_STEM_W = 0.011
BUTTON_STEM_D = 0.007
BUTTON_STEM_H = 0.0026
def _body_shell() -> cq.Workplane:
    body = (
        cq.Workplane("XY")
        .box(BODY_W, BODY_D, BODY_H, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.011)
    )

    control_strip = (
        cq.Workplane("XY")
        .box(CONTROL_STRIP_W, CONTROL_STRIP_D, CONTROL_STRIP_H, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.004)
        .translate((0.0, CONTROL_Y, BODY_H))
    )
    body = body.union(control_strip)

    scanner_cut = (
        cq.Workplane("XY")
        .box(
            SCANNER_OPENING_W,
            SCANNER_OPENING_D,
            SCANNER_RECESS + 0.001,
            centered=(True, True, False),
        )
        .translate((0.0, SCANNER_CENTER_Y, BODY_H - SCANNER_RECESS))
    )
    body = body.cut(scanner_cut)

    paper_path_cut = (
        cq.Workplane("XY")
        .box(0.286, 0.304, 0.019, centered=(True, True, True))
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 17.0)
        .translate((0.0, -0.016, 0.046))
    )
    body = body.cut(paper_path_cut)

    front_mouth_cut = (
        cq.Workplane("XY")
        .box(0.292, 0.080, 0.028, centered=(True, True, True))
        .translate((0.0, -BODY_D / 2.0 - 0.018, 0.060))
    )
    body = body.cut(front_mouth_cut)

    rear_feed_cut = (
        cq.Workplane("XY")
        .box(0.276, 0.070, 0.024, centered=(True, True, True))
        .translate((0.0, BODY_D / 2.0 - 0.012, BODY_H - 0.004))
    )
    body = body.cut(rear_feed_cut)

    dial_well = (
        cq.Workplane("XY")
        .circle(DIAL_R + 0.0025)
        .extrude(0.002)
        .translate((DIAL_X, CONTROL_Y, CONTROL_TOP_Z - 0.002))
    )
    body = body.cut(dial_well)

    for button_x in BUTTON_XS:
        button_well = (
            cq.Workplane("XY")
            .box(BUTTON_STEM_W + 0.0015, BUTTON_STEM_D + 0.0015, 0.0048, centered=(True, True, False))
            .translate((button_x, CONTROL_Y, CONTROL_TOP_Z - 0.0048))
        )
        body = body.cut(button_well)

    return body
def _lid_shell() -> cq.Workplane:
    outer = (
        cq.Workplane("XY")
        .box(LID_W, LID_D, LID_T, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.0045)
    )

    underside_cut = (
        cq.Workplane("XY")
        .box(LID_W - 0.036, LID_D - 0.028, 0.0105, centered=(True, True, False))
        .translate((0.0, -0.006, 0.0))
    )
    hinge_foot = (
        cq.Workplane("XY")
        .box(LID_W - 0.060, 0.006, 0.0013, centered=(True, True, False))
        .translate((0.0, LID_D / 2.0 - 0.004, -0.0012))
    )
    return outer.cut(underside_cut).union(hinge_foot)
def _rear_guide() -> cq.Workplane:
    panel = (
        cq.Workplane("XY")
        .box(GUIDE_W, GUIDE_D, GUIDE_T, centered=(True, False, False))
    )
    guide = panel

    rear_rib = (
        cq.Workplane("XY")
        .box(GUIDE_W, 0.010, 0.012, centered=(True, False, False))
        .translate((0.0, GUIDE_D - 0.010, GUIDE_T))
    )
    guide = guide.union(rear_rib)

    side_rib_l = (
        cq.Workplane("XY")
        .box(0.005, GUIDE_D, 0.011, centered=(True, False, False))
        .translate((-(GUIDE_W / 2.0 - 0.0025), 0.0, GUIDE_T))
    )
    side_rib_r = (
        cq.Workplane("XY")
        .box(0.005, GUIDE_D, 0.011, centered=(True, False, False))
        .translate(((GUIDE_W / 2.0 - 0.0025), 0.0, GUIDE_T))
    )
    return guide.union(side_rib_l).union(side_rib_r)
def _tray_shell() -> cq.Workplane:
    floor = (
        cq.Workplane("XY")
        .box(TRAY_W, TRAY_D, TRAY_T, centered=(True, False, False))
        .translate((0.0, -TRAY_D, 0.0))
    )

    side_l = (
        cq.Workplane("XY")
        .box(TRAY_WALL, TRAY_D, 0.012, centered=(True, False, False))
        .translate((-(TRAY_W / 2.0 - TRAY_WALL / 2.0), -TRAY_D, TRAY_T))
    )
    side_r = (
        cq.Workplane("XY")
        .box(TRAY_WALL, TRAY_D, 0.012, centered=(True, False, False))
        .translate(((TRAY_W / 2.0 - TRAY_WALL / 2.0), -TRAY_D, TRAY_T))
    )
    front_lip = (
        cq.Workplane("XY")
        .box(TRAY_W, TRAY_WALL, TRAY_LIP, centered=(True, False, False))
        .translate((0.0, -TRAY_D, TRAY_T))
    )
    return floor.union(side_l).union(side_r).union(front_lip)
def _dial_knob() -> cq.Workplane:
    base = cq.Workplane("XY").circle(DIAL_R).extrude(0.011)
    cap = cq.Workplane("XY").circle(DIAL_R - 0.0035).extrude(0.004).translate((0.0, 0.0, 0.011))
    stem = cq.Workplane("XY").circle(0.006).extrude(0.002).translate((0.0, 0.0, -0.002))
    pointer = (
        cq.Workplane("XY")
        .box(0.0035, 0.010, 0.0016, centered=(True, False, False))
        .translate((0.0, 0.002, DIAL_H - 0.0016))
    )
    return base.union(cap).union(stem).union(pointer)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="wireless_home_printer")

    model.material("shell", rgba=(0.91, 0.92, 0.93, 1.0))
    model.material("trim", rgba=(0.21, 0.23, 0.26, 1.0))
    model.material("button", rgba=(0.15, 0.17, 0.19, 1.0))
    model.material("glass", rgba=(0.52, 0.60, 0.68, 0.50))
    model.material("scanner_bed", rgba=(0.09, 0.10, 0.11, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shell(), "printer_body"),
        material="shell",
        name="body_shell",
    )
    body.visual(
        Box((GLASS_W + 0.018, GLASS_D + 0.018, 0.0012)),
        origin=Origin(xyz=(0.0, SCANNER_CENTER_Y, BODY_H - SCANNER_RECESS + 0.0006)),
        material="scanner_bed",
        name="scanner_bed",
    )
    body.visual(
        Box((GLASS_W, GLASS_D, GLASS_T)),
        origin=Origin(xyz=(0.0, SCANNER_CENTER_Y, BODY_H - SCANNER_RECESS + 0.0012 + GLASS_T / 2.0)),
        material="glass",
        name="scanner_glass",
    )

    lid = model.part("lid")
    lid.visual(
        mesh_from_cadquery(_lid_shell(), "printer_lid"),
        origin=Origin(xyz=(0.0, -LID_D / 2.0, 0.0)),
        material="shell",
        name="lid_shell",
    )

    rear_guide = model.part("rear_guide")
    rear_guide.visual(
        mesh_from_cadquery(_rear_guide(), "printer_rear_guide"),
        material="shell",
        name="guide_shell",
    )

    tray = model.part("tray")
    tray.visual(
        mesh_from_cadquery(_tray_shell(), "printer_tray"),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material="trim",
        name="tray_shell",
    )

    dial = model.part("dial")
    dial.visual(
        mesh_from_cadquery(_dial_knob(), "printer_dial"),
        material="trim",
        name="dial_knob",
    )

    for idx, button_x in enumerate(BUTTON_XS):
        button = model.part(f"button_{idx}")
        button.visual(
            Box((BUTTON_W, BUTTON_D, BUTTON_H)),
            origin=Origin(xyz=(0.0, 0.0, BUTTON_H / 2.0)),
            material="button",
            name="button_cap",
        )
        button.visual(
            Box((BUTTON_STEM_W, BUTTON_STEM_D, BUTTON_STEM_H)),
            origin=Origin(xyz=(0.0, 0.0, -BUTTON_STEM_H / 2.0)),
            material="button",
            name="button_stem",
        )
        model.articulation(
            f"body_to_button_{idx}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(xyz=(button_x, CONTROL_Y, CONTROL_TOP_Z)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                lower=0.0,
                upper=BUTTON_TRAVEL,
                effort=6.0,
                velocity=0.05,
            ),
        )

    model.articulation(
        "body_to_lid",
        ArticulationType.REVOLUTE,
        parent=body,
        child=lid,
        origin=Origin(xyz=(0.0, LID_HINGE_Y, LID_HINGE_Z)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.22, effort=16.0, velocity=1.4),
    )
    model.articulation(
        "body_to_rear_guide",
        ArticulationType.REVOLUTE,
        parent=body,
        child=rear_guide,
        origin=Origin(xyz=(0.0, GUIDE_HINGE_Y, GUIDE_HINGE_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.10, effort=8.0, velocity=1.4),
    )
    model.articulation(
        "body_to_tray",
        ArticulationType.REVOLUTE,
        parent=body,
        child=tray,
        origin=Origin(xyz=(0.0, -BODY_D / 2.0, TRAY_HINGE_Z)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.35, effort=8.0, velocity=1.8),
    )
    model.articulation(
        "body_to_dial",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=dial,
        origin=Origin(xyz=(DIAL_X, CONTROL_Y, CONTROL_TOP_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=1.0, velocity=4.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
