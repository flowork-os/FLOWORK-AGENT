# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_flash, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_flash

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
BODY_WIDTH = 0.074
BODY_DEPTH = 0.046
BODY_HEIGHT = 0.102
BODY_BOTTOM_Z = 0.030
COLLAR_TOP_Z = 0.148
YOKE_TRUNNION_Z = 0.034
HEAD_WIDTH = 0.068
HEAD_DEPTH = 0.050
HEAD_HEIGHT = 0.040
def _body_shape() -> cq.Workplane:
    shell = (
        cq.Workplane("XY")
        .box(BODY_WIDTH, BODY_DEPTH, BODY_HEIGHT, centered=(True, True, False))
        .translate((0.0, 0.0, BODY_BOTTOM_Z))
    )
    shell = shell.edges("|Z").fillet(0.006)

    neck = (
        cq.Workplane("XY")
        .box(0.056, 0.036, 0.012, centered=(True, True, False))
        .translate((0.0, 0.0, BODY_BOTTOM_Z + BODY_HEIGHT))
    )
    neck = neck.edges("|Z").fillet(0.004)

    collar = (
        cq.Workplane("XY")
        .circle(0.018)
        .extrude(COLLAR_TOP_Z - (BODY_BOTTOM_Z + BODY_HEIGHT + 0.012))
        .translate((0.0, 0.0, BODY_BOTTOM_Z + BODY_HEIGHT + 0.012))
    )

    foot_plate = (
        cq.Workplane("XY")
        .box(0.054, 0.042, 0.006, centered=(True, True, False))
        .translate((0.0, 0.0, 0.0))
    )
    foot_rail = (
        cq.Workplane("XY")
        .box(0.022, 0.032, 0.012, centered=(True, True, False))
        .translate((0.0, 0.0, 0.006))
    )
    foot_stem = (
        cq.Workplane("XY")
        .box(0.032, 0.028, BODY_BOTTOM_Z - 0.018, centered=(True, True, False))
        .translate((0.0, 0.0, 0.018))
    )

    body = shell.union(neck).union(collar).union(foot_plate).union(foot_rail).union(foot_stem)

    control_pocket = (
        cq.Workplane("XY")
        .box(0.056, 0.008, 0.074, centered=(True, True, False))
        .translate((0.0, -(BODY_DEPTH * 0.5) + 0.0035, 0.042))
    )
    return body.cut(control_pocket)
def _head_shape() -> cq.Workplane:
    shell = (
        cq.Workplane("XY")
        .box(HEAD_WIDTH, HEAD_DEPTH, HEAD_HEIGHT, centered=(True, True, True))
        .translate((0.0, 0.018, 0.0))
    )
    shell = shell.edges("|Z").fillet(0.004)
    shell = shell.edges("|X").fillet(0.003)

    shell = (
        shell.faces(">Y")
        .workplane()
        .rect(0.056, 0.026)
        .cutBlind(0.002)
    )

    trunnions = cq.Workplane("YZ").circle(0.006).extrude(0.039, both=True)
    return shell.union(trunnions)
def _yoke_shape() -> cq.Workplane:
    base = cq.Workplane("XY").circle(0.016).extrude(0.008)
    pedestal = (
        cq.Workplane("XY")
        .box(0.040, 0.024, 0.008, centered=(True, True, False))
        .translate((0.0, 0.0, 0.008))
    )
    spine = (
        cq.Workplane("XY")
        .box(0.018, 0.006, 0.022, centered=(True, True, False))
        .translate((0.0, -0.014, 0.016))
    )
    crossbar = (
        cq.Workplane("XY")
        .box(0.088, 0.006, 0.010, centered=(True, True, False))
        .translate((0.0, -0.014, 0.030))
    )
    return base.union(pedestal).union(spine).union(crossbar)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="camera_flash")

    model.material("body_black", rgba=(0.12, 0.12, 0.13, 1.0))
    model.material("trim_dark", rgba=(0.18, 0.18, 0.19, 1.0))
    model.material("diffuser", rgba=(0.92, 0.93, 0.95, 0.78))
    model.material("screen_glass", rgba=(0.26, 0.40, 0.46, 0.55))
    model.material("button_dark", rgba=(0.24, 0.24, 0.25, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shape(), "flash_body"),
        material="body_black",
        name="shell",
    )
    body.visual(
        Box((0.032, 0.0040, 0.022)),
        origin=Origin(xyz=(0.0, -0.0175, 0.090)),
        material="trim_dark",
        name="screen_frame",
    )
    body.visual(
        Box((0.028, 0.0018, 0.018)),
        origin=Origin(xyz=(0.0, -0.0196, 0.090)),
        material="screen_glass",
        name="screen",
    )

    yoke = model.part("yoke")
    yoke.visual(
        mesh_from_cadquery(_yoke_shape(), "flash_yoke"),
        material="trim_dark",
        name="frame",
    )

    for index, arm_x in enumerate((-0.0435, 0.0435)):
        arm = model.part(f"arm_{index}")
        arm.visual(
            Box((0.007, 0.022, 0.036)),
            origin=Origin(xyz=(0.0, 0.0, 0.018)),
            material="trim_dark",
            name="arm",
        )
        arm.visual(
            Cylinder(radius=0.0065, length=0.007),
            origin=Origin(xyz=(0.0, 0.0, YOKE_TRUNNION_Z), rpy=(0.0, math.pi * 0.5, 0.0)),
            material="trim_dark",
            name="pivot_cap",
        )
        model.articulation(
            f"yoke_to_arm_{index}",
            ArticulationType.FIXED,
            parent=yoke,
            child=arm,
            origin=Origin(xyz=(arm_x, 0.0, 0.008)),
        )

    head = model.part("head")
    head.visual(
        mesh_from_cadquery(_head_shape(), "flash_head"),
        material="body_black",
        name="shell",
    )
    head.visual(
        Box((0.054, 0.0030, 0.026)),
        origin=Origin(xyz=(0.0, 0.0410, 0.0)),
        material="diffuser",
        name="diffuser",
    )

    model.articulation(
        "body_to_yoke",
        ArticulationType.REVOLUTE,
        parent=body,
        child=yoke,
        origin=Origin(xyz=(0.0, 0.0, COLLAR_TOP_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=6.0,
            velocity=2.0,
            lower=-math.radians(120.0),
            upper=math.radians(120.0),
        ),
    )
    model.articulation(
        "yoke_to_head",
        ArticulationType.REVOLUTE,
        parent=yoke,
        child=head,
        origin=Origin(xyz=(0.0, 0.0, YOKE_TRUNNION_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=5.0,
            velocity=2.0,
            lower=-math.radians(15.0),
            upper=math.radians(110.0),
        ),
    )

    button_specs = (
        ("button_0", (-0.021, 0.100), (0.010, 0.0035, 0.008)),
        ("button_1", (-0.021, 0.082), (0.010, 0.0035, 0.008)),
        ("button_2", (0.021, 0.100), (0.010, 0.0035, 0.008)),
        ("button_3", (0.021, 0.082), (0.010, 0.0035, 0.008)),
        ("button_4", (-0.010, 0.064), (0.012, 0.0038, 0.006)),
        ("button_5", (0.010, 0.064), (0.012, 0.0038, 0.006)),
        ("button_6", (0.000, 0.049), (0.014, 0.0038, 0.008)),
    )
    for button_name, (button_x, button_z), button_size in button_specs:
        button = model.part(button_name)
        button.visual(
            Box(button_size),
            origin=Origin(xyz=(0.0, -(button_size[1] * 0.5), 0.0)),
            material="button_dark",
            name="cap",
        )
        button.visual(
            Box((min(button_size[0] * 0.5, 0.006), 0.0030, min(button_size[2] * 0.7, 0.005))),
            origin=Origin(xyz=(0.0, 0.0015, 0.0)),
            material="button_dark",
            name="stem",
        )
        model.articulation(
            f"body_to_{button_name}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(xyz=(button_x, -0.0185, button_z)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(
                effort=1.2,
                velocity=0.04,
                lower=0.0,
                upper=0.0015,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
