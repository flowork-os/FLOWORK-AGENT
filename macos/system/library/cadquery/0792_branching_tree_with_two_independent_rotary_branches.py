# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, branching_tree_with_two_independent_rotary_branches, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: branching_tree_with_two_independent_rotary_branches

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
BASE_FOOT_SIZE = (0.32, 0.14, 0.03)
BASE_COLUMN_SIZE = (0.08, 0.10, 0.16)
BASE_TOP_BEAM_SIZE = (0.24, 0.08, 0.05)
BASE_SHOULDER_BLOCK_SIZE = (0.06, 0.08, 0.05)
SHOULDER_Z = 0.215
SHOULDER_X = 0.15
UPPER_ARM_SPAN = 0.18
FOREARM_SPAN = 0.164
def _barrel_on_y(radius: float, length: float, x: float = 0.0, z: float = 0.0) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length)
        .translate((0.0, 0.0, -0.5 * length))
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
        .translate((x, 0.0, z))
    )
def _arm_beam(
    length: float, width: float, height: float, x_center: float, z_center: float = 0.0
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(length, width, height)
        .edges("|Z")
        .fillet(min(width, height) * 0.24)
        .translate((x_center, 0.0, z_center))
    )
def _barrel_on_x(radius: float, length: float, x: float = 0.0, z: float = 0.0) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length)
        .translate((0.0, 0.0, -0.5 * length))
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -90.0)
        .translate((x, 0.0, z))
    )
def _make_base_visual() -> cq.Workplane:
    foot = (
        cq.Workplane("XY")
        .box(*BASE_FOOT_SIZE)
        .edges("|Z")
        .fillet(0.012)
        .edges("#Z")
        .fillet(0.005)
        .translate((0.0, 0.0, 0.5 * BASE_FOOT_SIZE[2]))
    )
    column = (
        cq.Workplane("XY")
        .box(*BASE_COLUMN_SIZE)
        .edges("|Z")
        .fillet(0.01)
        .translate((0.0, 0.0, BASE_FOOT_SIZE[2] + 0.5 * BASE_COLUMN_SIZE[2]))
    )
    top_beam = (
        cq.Workplane("XY")
        .box(*BASE_TOP_BEAM_SIZE)
        .edges("|Z")
        .fillet(0.008)
        .translate((0.0, 0.0, SHOULDER_Z))
    )
    left_block = (
        cq.Workplane("XY")
        .box(*BASE_SHOULDER_BLOCK_SIZE)
        .edges("|Z")
        .fillet(0.006)
        .translate((-0.12, 0.0, SHOULDER_Z))
    )
    right_block = (
        cq.Workplane("XY")
        .box(*BASE_SHOULDER_BLOCK_SIZE)
        .edges("|Z")
        .fillet(0.006)
        .translate((0.12, 0.0, SHOULDER_Z))
    )
    left_brace = (
        cq.Workplane("XY")
        .box(0.11, 0.035, 0.03)
        .edges("|Y")
        .fillet(0.006)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -30.0)
        .translate((-0.058, 0.0, 0.173))
    )
    right_brace = (
        cq.Workplane("XY")
        .box(0.11, 0.035, 0.03)
        .edges("|Y")
        .fillet(0.006)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 30.0)
        .translate((0.058, 0.0, 0.173))
    )
    return (
        foot.union(column)
        .union(top_beam)
        .union(left_block)
        .union(right_block)
        .union(left_brace)
        .union(right_brace)
    )
def _make_upper_arm_visual(sign: float) -> cq.Workplane:
    direction = 1.0 if sign >= 0.0 else -1.0
    inner_barrel = _barrel_on_y(radius=0.026, length=0.052)
    beam = _arm_beam(length=0.13, width=0.04, height=0.05, x_center=direction * 0.09)
    mid_rib = (
        cq.Workplane("XY")
        .box(0.10, 0.022, 0.06)
        .edges("|Y")
        .fillet(0.004)
        .translate((direction * 0.10, 0.0, 0.005))
    )
    elbow_block = (
        cq.Workplane("XY")
        .box(0.046, 0.05, 0.056)
        .edges("|Z")
        .fillet(0.007)
        .translate((direction * UPPER_ARM_SPAN, 0.0, 0.0))
    )
    elbow_barrel = _barrel_on_y(radius=0.024, length=0.05, x=direction * UPPER_ARM_SPAN)
    return inner_barrel.union(beam).union(mid_rib).union(elbow_block).union(elbow_barrel)
def _make_forearm_visual(sign: float) -> cq.Workplane:
    direction = 1.0 if sign >= 0.0 else -1.0
    elbow_barrel = _barrel_on_y(radius=0.023, length=0.048)
    beam = _arm_beam(length=0.105, width=0.033, height=0.043, x_center=direction * 0.078)
    taper = (
        cq.Workplane("XY")
        .box(0.058, 0.028, 0.036)
        .edges("|Z")
        .fillet(0.005)
        .translate((direction * 0.136, 0.0, 0.0))
    )
    tip = _barrel_on_x(radius=0.018, length=0.024, x=direction * FOREARM_SPAN)
    return elbow_barrel.union(beam).union(taper).union(tip)
def _add_visual_mesh(part, shape: cq.Workplane, filename: str, material: str) -> None:
    part.visual(mesh_from_cadquery(shape, filename, assets=ASSETS), material=material)
def _add_base_collisions(base) -> None:
    pass
def _add_upper_arm_collisions(part, sign: float) -> None:
    direction = 1.0 if sign >= 0.0 else -1.0
    pass
def _add_forearm_collisions(part, sign: float) -> None:
    direction = 1.0 if sign >= 0.0 else -1.0
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="branching_dual_arm", assets=ASSETS)

    model.material("graphite", rgba=(0.24, 0.25, 0.29, 1.0))
    model.material("left_branch", rgba=(0.9, 0.46, 0.14, 1.0))
    model.material("right_branch", rgba=(0.18, 0.47, 0.84, 1.0))
    model.material("link_dark", rgba=(0.35, 0.37, 0.40, 1.0))

    base = model.part("base")
    _add_visual_mesh(base, _make_base_visual(), "base_structure.obj", "graphite")
    _add_base_collisions(base)
    base.inertial = Inertial.from_geometry(
        Box((0.28, 0.14, 0.24)),
        mass=3.6,
        origin=Origin(xyz=(0.0, 0.0, 0.12)),
    )

    left_upper_arm = model.part("left_upper_arm")
    _add_visual_mesh(
        left_upper_arm, _make_upper_arm_visual(sign=-1.0), "left_upper_arm.obj", "left_branch"
    )
    _add_upper_arm_collisions(left_upper_arm, sign=-1.0)
    left_upper_arm.inertial = Inertial.from_geometry(
        Box((0.18, 0.05, 0.055)),
        mass=0.62,
        origin=Origin(xyz=(-0.09, 0.0, 0.0)),
    )

    left_forearm = model.part("left_forearm")
    _add_visual_mesh(left_forearm, _make_forearm_visual(sign=-1.0), "left_forearm.obj", "link_dark")
    _add_forearm_collisions(left_forearm, sign=-1.0)
    left_forearm.inertial = Inertial.from_geometry(
        Box((0.16, 0.04, 0.045)),
        mass=0.4,
        origin=Origin(xyz=(-0.08, 0.0, 0.0)),
    )

    right_upper_arm = model.part("right_upper_arm")
    _add_visual_mesh(
        right_upper_arm, _make_upper_arm_visual(sign=1.0), "right_upper_arm.obj", "right_branch"
    )
    _add_upper_arm_collisions(right_upper_arm, sign=1.0)
    right_upper_arm.inertial = Inertial.from_geometry(
        Box((0.18, 0.05, 0.055)),
        mass=0.62,
        origin=Origin(xyz=(0.09, 0.0, 0.0)),
    )

    right_forearm = model.part("right_forearm")
    _add_visual_mesh(
        right_forearm, _make_forearm_visual(sign=1.0), "right_forearm.obj", "link_dark"
    )
    _add_forearm_collisions(right_forearm, sign=1.0)
    right_forearm.inertial = Inertial.from_geometry(
        Box((0.16, 0.04, 0.045)),
        mass=0.4,
        origin=Origin(xyz=(0.08, 0.0, 0.0)),
    )

    model.articulation(
        "base_to_left_upper",
        ArticulationType.REVOLUTE,
        parent=base,
        child=left_upper_arm,
        origin=Origin(xyz=(-SHOULDER_X, 0.0, SHOULDER_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.2, effort=12.0, velocity=1.4),
    )
    model.articulation(
        "left_upper_to_forearm",
        ArticulationType.REVOLUTE,
        parent=left_upper_arm,
        child=left_forearm,
        origin=Origin(xyz=(-UPPER_ARM_SPAN, 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.45, effort=9.0, velocity=1.8),
    )
    model.articulation(
        "base_to_right_upper",
        ArticulationType.REVOLUTE,
        parent=base,
        child=right_upper_arm,
        origin=Origin(xyz=(SHOULDER_X, 0.0, SHOULDER_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.2, effort=12.0, velocity=1.4),
    )
    model.articulation(
        "right_upper_to_forearm",
        ArticulationType.REVOLUTE,
        parent=right_upper_arm,
        child=right_forearm,
        origin=Origin(xyz=(UPPER_ARM_SPAN, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.45, effort=9.0, velocity=1.8),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
