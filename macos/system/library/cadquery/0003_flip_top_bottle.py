# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, flip_top_bottle, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: flip_top_bottle

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

class Inertia:
    def __init__(self, ixx=0.0, ixy=0.0, ixz=0.0, iyy=0.0, iyz=0.0, izz=0.0):
        self.ixx, self.ixy, self.ixz = ixx, ixy, ixz
        self.iyy, self.iyz, self.izz = iyy, iyz, izz

class Inertial:
    def __init__(self, mass=1.0, inertia=None, origin=None):
        self.mass = float(mass)
        self.inertia = inertia
        self.origin = origin or Origin()

    @staticmethod
    def from_geometry(geometry, mass, *, origin=None):
        return Inertial(mass=mass, inertia=Inertia(), origin=origin or Origin())

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

class _NoOp:
    """Universal no-op sentinel that is callable AND Path-like, so asset/IO
    expressions in model scripts (e.g. ASSETS.mesh_dir.mkdir(); dir / 'x.obj')
    are harmless in self-contained mode."""
    def __call__(self, *a, **k):
        return self

    def __getattr__(self, _n):
        return self

    def __truediv__(self, _o):
        return self

    def __rtruediv__(self, _o):
        return self

    def __fspath__(self):
        return "/tmp/_articraft_noop"

    def mkdir(self, *a, **k):
        return None

_NOOP = _NoOp()

class _NoopMeta(type):
    def __getattr__(cls, _name):
        def _noop(*a, **k):
            return cls()
        return _noop

class AssetContext(metaclass=_NoopMeta):
    def __init__(self, *a, **k):
        pass

    def __getattr__(self, _n):
        return _NOOP

# ===== model =====
import cadquery as cq
ASSETS = AssetContext.from_script(__file__)
BODY_LENGTH = 0.078
BODY_WIDTH = 0.032
SHOULDER_SWELL = 0.013
BODY_HEIGHT = 0.112
BODY_WALL = 0.0018
VERTICAL_FILLET = 0.0045
NECK_RADIUS = 0.012
NECK_HEIGHT = 0.020
NECK_BEAD_RADIUS = 0.0134
NECK_BEAD_HEIGHT = 0.0024
FRAME_HEIGHT = 0.010
FRAME_OUTER_RADIUS = 0.0144
FRAME_INNER_RADIUS = 0.0118
FRAME_LATCH_WIDTH = 0.012
FRAME_LATCH_DEPTH = 0.003
FRAME_LATCH_HEIGHT = 0.003
CAP_HEIGHT = 0.025
CAP_OUTER_RADIUS = 0.0170
CAP_INNER_RADIUS = 0.0152
CAP_WALL = 0.0018
HINGE_PIN_RADIUS = 0.0026
BODY_LUG_LENGTH = 0.0065
CAP_KNUCKLE_LENGTH = 0.0100
BODY_LUG_X = 0.0088
CAP_CENTER_Y = 0.0180
CAP_CENTER_Z = 0.0060
HINGE_Y = -CAP_CENTER_Y
HINGE_Z = BODY_HEIGHT + NECK_HEIGHT + 0.0048
def _make_glass_bottle() -> cq.Workplane:
    bottle_blank = (
        cq.Workplane("XY")
        .center(-BODY_LENGTH / 2.0, 0.0)
        .vLine(BODY_WIDTH / 2.0)
        .threePointArc(
            (BODY_LENGTH / 2.0, BODY_WIDTH / 2.0 + SHOULDER_SWELL),
            (BODY_LENGTH, BODY_WIDTH / 2.0),
        )
        .vLine(-BODY_WIDTH / 2.0)
        .mirrorX()
        .extrude(BODY_HEIGHT)
        .edges("|Z")
        .fillet(VERTICAL_FILLET)
        .faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .circle(NECK_RADIUS)
        .extrude(NECK_HEIGHT)
    )

    hollow = bottle_blank.faces(">Z").shell(BODY_WALL)
    bead = (
        cq.Workplane("XY")
        .circle(NECK_BEAD_RADIUS)
        .circle(NECK_RADIUS)
        .extrude(NECK_BEAD_HEIGHT)
        .translate((0.0, 0.0, BODY_HEIGHT + NECK_HEIGHT - 0.006))
    )
    return hollow.union(bead)
def _make_neck_frame() -> cq.Workplane:
    collar = (
        cq.Workplane("XY")
        .circle(FRAME_OUTER_RADIUS)
        .circle(FRAME_INNER_RADIUS)
        .extrude(FRAME_HEIGHT)
        .translate((0.0, 0.0, BODY_HEIGHT + NECK_HEIGHT - FRAME_HEIGHT))
    )

    front_latch = (
        cq.Workplane("XY")
        .box(FRAME_LATCH_WIDTH, FRAME_LATCH_DEPTH, FRAME_LATCH_HEIGHT)
        .translate(
            (
                0.0,
                FRAME_OUTER_RADIUS - 0.0012,
                BODY_HEIGHT + NECK_HEIGHT - 0.0034,
            )
        )
    )

    rear_bridge = (
        cq.Workplane("XY")
        .box(0.022, 0.0045, 0.0045)
        .translate((0.0, -0.0133, BODY_HEIGHT + NECK_HEIGHT - 0.0044))
    )

    support_arms = []
    hinge_lugs = []
    for lug_x in (-BODY_LUG_X, BODY_LUG_X):
        support_arms.append(
            cq.Workplane("XY")
            .box(BODY_LUG_LENGTH, 0.0044, 0.0120)
            .translate((lug_x, -0.0139, HINGE_Z - 0.0060))
        )
        hinge_lugs.append(
            cq.Workplane("YZ")
            .circle(HINGE_PIN_RADIUS)
            .extrude(BODY_LUG_LENGTH / 2.0, both=True)
            .translate((lug_x, HINGE_Y, HINGE_Z))
        )

    frame = collar.union(front_latch).union(rear_bridge)
    for arm in support_arms:
        frame = frame.union(arm)
    for lug in hinge_lugs:
        frame = frame.union(lug)
    return frame
def _make_cap() -> cq.Workplane:
    cap_outer = (
        cq.Workplane("XY")
        .circle(CAP_OUTER_RADIUS)
        .extrude(CAP_HEIGHT)
        .faces(">Z")
        .edges()
        .fillet(0.0015)
        .translate((0.0, CAP_CENTER_Y, CAP_CENTER_Z - CAP_HEIGHT / 2.0))
    )

    cap_inner = (
        cq.Workplane("XY")
        .circle(CAP_INNER_RADIUS)
        .extrude(CAP_HEIGHT - CAP_WALL)
        .translate((0.0, CAP_CENTER_Y, CAP_CENTER_Z - CAP_HEIGHT / 2.0))
    )

    shell = cap_outer.cut(cap_inner)

    knuckle = (
        cq.Workplane("YZ")
        .circle(HINGE_PIN_RADIUS)
        .extrude(CAP_KNUCKLE_LENGTH / 2.0, both=True)
    )

    web = (
        cq.Workplane("XY")
        .box(CAP_KNUCKLE_LENGTH, 0.018, 0.0055)
        .translate((0.0, 0.0082, 0.0022))
    )

    thumb_tab = (
        cq.Workplane("XY")
        .box(0.018, 0.006, 0.0038)
        .edges("|X")
        .fillet(0.0011)
        .translate(
            (
                0.0,
                CAP_CENTER_Y + CAP_OUTER_RADIUS * 0.68,
                CAP_CENTER_Z + CAP_HEIGHT * 0.18,
            )
        )
    )

    top_button = (
        cq.Workplane("XY")
        .circle(0.0065)
        .extrude(0.0014)
        .translate(
            (0.0, CAP_CENTER_Y + 0.0015, CAP_CENTER_Z + CAP_HEIGHT / 2.0 - 0.0007)
        )
    )

    return shell.union(knuckle).union(web).union(thumb_tab).union(top_button)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="classic_occ_bottle_with_articulated_cap", assets=ASSETS)

    glass = model.material("glass", rgba=(0.58, 0.79, 0.72, 0.42))
    charcoal = model.material("charcoal", rgba=(0.10, 0.11, 0.13, 1.0))

    bottle = model.part("bottle")
    bottle.visual(
        mesh_from_cadquery(_make_glass_bottle(), "bottle_glass.obj", assets=ASSETS),
        material=glass,
    )
    bottle.visual(
        mesh_from_cadquery(_make_neck_frame(), "bottle_frame.obj", assets=ASSETS),
        material=charcoal,
    )
    bottle.inertial = Inertial.from_geometry(
        Box((BODY_LENGTH, BODY_WIDTH, BODY_HEIGHT + NECK_HEIGHT)),
        mass=0.32,
        origin=Origin(xyz=(0.0, 0.0, (BODY_HEIGHT + NECK_HEIGHT) / 2.0)),
    )

    cap = model.part("cap")
    cap.visual(
        mesh_from_cadquery(_make_cap(), "cap.obj", assets=ASSETS),
        material=charcoal,
    )
    cap.inertial = Inertial.from_geometry(
        Cylinder(radius=CAP_OUTER_RADIUS, length=CAP_HEIGHT),
        mass=0.05,
        origin=Origin(xyz=(0.0, CAP_CENTER_Y, CAP_CENTER_Z)),
    )

    model.articulation(
        "cap_hinge",
        ArticulationType.REVOLUTE,
        parent="bottle",
        child="cap",
        origin=Origin(xyz=(0.0, HINGE_Y, HINGE_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=2.0,
            velocity=2.5,
            lower=0.0,
            upper=2.1,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
