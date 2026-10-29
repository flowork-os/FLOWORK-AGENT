# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bread_maker_with_hinged_lid, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bread_maker_with_hinged_lid

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

class Cylinder:
    __slots__ = ("radius", "length")

    def __init__(self, radius, length=None, *, height=None):
        self.radius = float(radius)
        self.length = float(height if length is None else length)

    @property
    def height(self):
        return self.length

    def _cq(self):
        return cq.Solid.makeCylinder(
            self.radius, self.length, cq.Vector(0, 0, -self.length / 2), cq.Vector(0, 0, 1)
        )

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
BODY_WIDTH = 0.39
BODY_DEPTH = 0.30
BODY_HEIGHT = 0.31
BODY_BASE_Z = 0.01
CHAMBER_WIDTH = 0.252
CHAMBER_DEPTH = 0.162
CHAMBER_FLOOR_Z = 0.105
FRONT_RECESS_DEPTH = 0.009
LID_WIDTH = 0.332
LID_DEPTH = 0.228
def _body_shape() -> cq.Workplane:
    shell = (
        cq.Workplane("XY")
        .box(BODY_WIDTH, BODY_DEPTH, BODY_HEIGHT - BODY_BASE_Z, centered=(True, True, False))
        .translate((0.0, 0.0, BODY_BASE_Z))
        .edges("|Z")
        .fillet(0.038)
        .edges(">Z")
        .fillet(0.018)
        .edges("<Z")
        .fillet(0.008)
    )

    for x_pos in (-0.125, 0.125):
        for y_pos in (-0.095, 0.095):
            foot = (
                cq.Workplane("XY")
                .box(0.055, 0.030, BODY_BASE_Z, centered=(True, True, False))
                .translate((x_pos, y_pos, 0.0))
            )
            shell = shell.union(foot)

    chamber_cutter = (
        cq.Workplane("XY")
        .box(CHAMBER_WIDTH, CHAMBER_DEPTH, BODY_HEIGHT - CHAMBER_FLOOR_Z + 0.01, centered=(True, True, False))
        .translate((0.0, 0.006, CHAMBER_FLOOR_Z))
        .edges("|Z")
        .fillet(0.020)
    )
    shell = shell.cut(chamber_cutter)

    spindle_hole = cq.Workplane("XY").circle(0.006).extrude(CHAMBER_FLOOR_Z + 0.004).translate((0.0, 0.006, 0.0))
    shell = shell.cut(spindle_hole)

    recess = (
        cq.Workplane("XY")
        .box(0.122, 0.012, 0.108, centered=(True, True, True))
        .translate((0.0, -BODY_DEPTH / 2.0 + 0.006, 0.136))
    )
    shell = shell.cut(recess)

    for x_pos in (-0.031, 0.031):
        mode_hole = (
            cq.Workplane("XY")
            .box(0.031, 0.022, 0.019, centered=(True, True, True))
            .translate((x_pos, -BODY_DEPTH / 2.0 + 0.011, 0.159))
        )
        shell = shell.cut(mode_hole)

    start_hole = (
        cq.Workplane("XY")
        .box(0.040, 0.022, 0.022, centered=(True, True, True))
        .translate((0.0, -BODY_DEPTH / 2.0 + 0.011, 0.121))
    )
    shell = shell.cut(start_hole)

    dial_recess = (
        cq.Workplane("YZ")
        .circle(0.034)
        .extrude(0.010)
        .translate((BODY_WIDTH / 2.0 - 0.010, -0.040, 0.196))
    )
    dial_hole = (
        cq.Workplane("YZ")
        .circle(0.010)
        .extrude(0.020)
        .translate((BODY_WIDTH / 2.0 - 0.020, -0.040, 0.196))
    )
    shell = shell.cut(dial_recess).cut(dial_hole)

    return shell
def _lid_shape() -> cq.Workplane:
    lid = (
        cq.Workplane("XY")
        .box(LID_WIDTH, LID_DEPTH, 0.040, centered=(True, True, False))
        .translate((0.0, -LID_DEPTH / 2.0, 0.004))
        .edges("|Z")
        .fillet(0.018)
        .edges(">Z")
        .fillet(0.010)
        .faces("<Z")
        .shell(-0.0035)
    )

    hinge_barrel = cq.Workplane("YZ").circle(0.0065).extrude(0.300).translate((-0.150, 0.0, 0.0))
    lid = lid.union(hinge_barrel)

    pocket = (
        cq.Workplane("XY")
        .box(0.108, 0.072, 0.042, centered=(True, True, False))
        .translate((0.086, -0.072, 0.006))
        .edges("|Z")
        .fillet(0.010)
    )
    return lid.cut(pocket)
def _dispenser_flap_shape() -> cq.Workplane:
    flap = (
        cq.Workplane("XY")
        .box(0.104, 0.066, 0.008, centered=(True, True, False))
        .translate((0.0, -0.033, -0.001))
        .edges("|Z")
        .fillet(0.006)
        .edges(">Z")
        .fillet(0.003)
    )
    barrel = cq.Workplane("YZ").circle(0.0068).extrude(0.090).translate((-0.045, 0.0, 0.0))
    return flap.union(barrel)
def _button_part(
    model: ArticulatedObject,
    name: str,
    size: tuple[float, float, float],
    material: str,
    visual_name: str,
    stem_name: str,
):
    button = model.part(name)
    button.visual(
        Box(size),
        origin=Origin(xyz=(0.0, size[1] / 2.0 - 0.002, 0.0)),
        material=material,
        name=visual_name,
    )
    button.visual(
        Box((size[0] * 0.72, 0.014, size[2] * 0.72)),
        origin=Origin(xyz=(0.0, 0.015, 0.0)),
        material=material,
        name=stem_name,
    )
    return button
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="wide_bread_maker")

    body_white = model.material("body_white", rgba=(0.92, 0.92, 0.90, 1.0))
    lid_white = model.material("lid_white", rgba=(0.96, 0.96, 0.94, 1.0))
    trim_gray = model.material("trim_gray", rgba=(0.55, 0.57, 0.60, 1.0))
    control_black = model.material("control_black", rgba=(0.12, 0.12, 0.13, 1.0))
    steel = model.material("steel", rgba=(0.76, 0.78, 0.80, 1.0))
    mode_gray = model.material("mode_gray", rgba=(0.70, 0.72, 0.74, 1.0))
    start_green = model.material("start_green", rgba=(0.19, 0.50, 0.27, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shape(), "body_shell"),
        material=body_white,
        name="body_shell",
    )

    lid = model.part("lid")
    lid.visual(
        mesh_from_cadquery(_lid_shape(), "lid_shell"),
        material=lid_white,
        name="lid_shell",
    )

    dispenser_flap = model.part("dispenser_flap")
    dispenser_flap.visual(
        mesh_from_cadquery(_dispenser_flap_shape(), "dispenser_flap"),
        material=trim_gray,
        name="flap_shell",
    )
    dispenser_flap.visual(
        Box((0.094, 0.008, 0.004)),
        origin=Origin(xyz=(0.0, 0.001, 0.0)),
        material=trim_gray,
        name="flap_hinge_tab",
    )

    spindle = model.part("spindle")
    spindle.visual(
        Cylinder(radius=0.017, length=0.006),
        origin=Origin(xyz=(0.0, 0.0, 0.006)),
        material=steel,
        name="spindle_hub",
    )
    spindle.visual(
        Cylinder(radius=0.006, length=0.006),
        origin=Origin(xyz=(0.0, 0.0, 0.003)),
        material=steel,
        name="spindle_pin",
    )
    spindle.visual(
        Cylinder(radius=0.005, length=0.028),
        origin=Origin(xyz=(0.0, 0.0, 0.020)),
        material=steel,
        name="spindle_shaft",
    )
    spindle.visual(
        Box((0.060, 0.010, 0.008)),
        origin=Origin(xyz=(0.0, 0.0, 0.013)),
        material=steel,
        name="kneader_bar",
    )
    spindle.visual(
        Box((0.010, 0.038, 0.008)),
        origin=Origin(xyz=(0.0, 0.0, 0.019)),
        material=steel,
        name="kneader_fin",
    )

    dial = model.part("dial")
    dial.visual(
        Cylinder(radius=0.035, length=0.004),
        origin=Origin(xyz=(0.002, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=trim_gray,
        name="dial_bezel",
    )
    dial.visual(
        Cylinder(radius=0.009, length=0.008),
        origin=Origin(xyz=(0.001, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=trim_gray,
        name="dial_shaft",
    )
    dial.visual(
        Cylinder(radius=0.026, length=0.018),
        origin=Origin(xyz=(0.013, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=control_black,
        name="dial_knob",
    )
    dial.visual(
        Box((0.004, 0.012, 0.006)),
        origin=Origin(xyz=(0.020, 0.017, 0.0)),
        material=steel,
        name="dial_pointer",
    )

    mode_button_0 = _button_part(
        model,
        name="mode_button_0",
        size=(0.026, 0.011, 0.015),
        material=mode_gray,
        visual_name="mode_button_cap_0",
        stem_name="mode_button_cap_0_stem",
    )
    mode_button_1 = _button_part(
        model,
        name="mode_button_1",
        size=(0.026, 0.011, 0.015),
        material=mode_gray,
        visual_name="mode_button_cap_1",
        stem_name="mode_button_cap_1_stem",
    )
    start_button = _button_part(
        model,
        name="start_button",
        size=(0.034, 0.012, 0.018),
        material=start_green,
        visual_name="start_button_cap",
        stem_name="start_button_cap_stem",
    )

    model.articulation(
        "body_to_lid",
        ArticulationType.REVOLUTE,
        parent=body,
        child=lid,
        origin=Origin(xyz=(0.0, 0.123, 0.316499)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.2,
            lower=0.0,
            upper=math.radians(112.0),
        ),
    )

    model.articulation(
        "body_to_spindle",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=spindle,
        origin=Origin(xyz=(0.0, 0.006, CHAMBER_FLOOR_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.5, velocity=18.0),
    )

    model.articulation(
        "body_to_dial",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=dial,
        origin=Origin(xyz=(BODY_WIDTH / 2.0 - 0.003, -0.040, 0.196)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.8, velocity=6.0),
    )

    model.articulation(
        "body_to_mode_button_0",
        ArticulationType.PRISMATIC,
        parent=body,
        child=mode_button_0,
        origin=Origin(xyz=(-0.031, -BODY_DEPTH / 2.0 + FRONT_RECESS_DEPTH + 0.002, 0.159)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=0.05, lower=0.0, upper=0.003),
    )

    model.articulation(
        "body_to_mode_button_1",
        ArticulationType.PRISMATIC,
        parent=body,
        child=mode_button_1,
        origin=Origin(xyz=(0.031, -BODY_DEPTH / 2.0 + FRONT_RECESS_DEPTH + 0.002, 0.159)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=0.05, lower=0.0, upper=0.003),
    )

    model.articulation(
        "body_to_start_button",
        ArticulationType.PRISMATIC,
        parent=body,
        child=start_button,
        origin=Origin(xyz=(0.0, -BODY_DEPTH / 2.0 + FRONT_RECESS_DEPTH + 0.002, 0.121)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=0.05, lower=0.0, upper=0.004),
    )

    model.articulation(
        "lid_to_dispenser_flap",
        ArticulationType.REVOLUTE,
        parent=lid,
        child=dispenser_flap,
        origin=Origin(xyz=(0.086, -0.036, 0.0319)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=1.0,
            velocity=2.0,
            lower=0.0,
            upper=math.radians(82.0),
        ),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
