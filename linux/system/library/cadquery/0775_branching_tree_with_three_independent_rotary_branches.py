# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, branching_tree_with_three_independent_rotary_branches, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: branching_tree_with_three_independent_rotary_branches

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

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
from math import cos, pi, sin
import cadquery as cq
ASSETS = AssetContext.from_script(__file__)
HUB_RADIUS = 0.046
HUB_HEIGHT = 0.054
HUB_RING_OUTER_RADIUS = 0.034
HUB_RING_INNER_RADIUS = 0.024
HUB_RING_HEIGHT = 0.008
SPINDLE_RADIUS = 0.017
SPINDLE_HEIGHT = 0.072
LUG_LENGTH = 0.034
LUG_WIDTH = 0.026
LUG_HEIGHT = 0.022
LUG_OFFSET_X = HUB_RADIUS + 0.5 * LUG_LENGTH - 0.008
JOINT_RADIUS = 0.058
BRANCH_ANGLES = (0.0, 2.0 * pi / 3.0, 4.0 * pi / 3.0)
BRANCH_NAMES = ("arm_a", "arm_b", "arm_c")
ARM_BARREL_RADIUS = 0.015
ARM_BARREL_LENGTH = 0.028
ARM_SHOULDER_LENGTH = 0.032
ARM_SHOULDER_WIDTH = 0.026
ARM_SHOULDER_HEIGHT = 0.018
ARM_SHOULDER_CENTER_X = 0.022
ARM_BODY_LENGTH = 0.118
ARM_BODY_WIDTH = 0.018
ARM_BODY_HEIGHT = 0.012
ARM_BODY_CENTER_X = 0.092
ARM_TIP_PAD_LENGTH = 0.026
ARM_TIP_PAD_WIDTH = 0.030
ARM_TIP_PAD_HEIGHT = 0.008
ARM_TIP_PAD_CENTER_X = 0.145
ARM_TIP_RADIUS = 0.014
ARM_TIP_X = 0.160
ARM_INERTIAL_LENGTH = 0.156
ARM_INERTIAL_WIDTH = 0.030
ARM_INERTIAL_HEIGHT = 0.022
ARM_INERTIAL_CENTER_X = 0.082
ARM_LIMITS = MotionLimits(lower=-0.65, upper=0.90, effort=8.0, velocity=1.5)
def _build_hub_shape() -> cq.Workplane:
    core = (
        cq.Workplane("XY")
        .circle(HUB_RADIUS)
        .extrude(HUB_HEIGHT)
        .translate((0.0, 0.0, -0.5 * HUB_HEIGHT))
    )
    spindle = (
        cq.Workplane("XY")
        .circle(SPINDLE_RADIUS)
        .extrude(SPINDLE_HEIGHT)
        .translate((0.0, 0.0, -0.5 * SPINDLE_HEIGHT))
    )
    ring = (
        cq.Workplane("XY")
        .circle(HUB_RING_OUTER_RADIUS)
        .circle(HUB_RING_INNER_RADIUS)
        .extrude(HUB_RING_HEIGHT)
        .translate((0.0, 0.0, -0.5 * HUB_RING_HEIGHT))
    )
    lug = (
        cq.Workplane("XY")
        .box(LUG_LENGTH, LUG_WIDTH, LUG_HEIGHT)
        .translate((LUG_OFFSET_X, 0.0, 0.0))
    )

    hub = core.union(spindle).union(ring)
    for angle_deg in (0.0, 120.0, 240.0):
        hub = hub.union(lug.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg))
    return hub
def _build_arm_shape() -> cq.Workplane:
    barrel = (
        cq.Workplane("XY")
        .circle(ARM_BARREL_RADIUS)
        .extrude(ARM_BARREL_LENGTH)
        .translate((0.0, 0.0, -0.5 * ARM_BARREL_LENGTH))
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -90.0)
    )
    shoulder = (
        cq.Workplane("XY")
        .box(
            ARM_SHOULDER_LENGTH,
            ARM_SHOULDER_WIDTH,
            ARM_SHOULDER_HEIGHT,
        )
        .translate((ARM_SHOULDER_CENTER_X, 0.0, 0.0))
    )
    beam = (
        cq.Workplane("XY")
        .box(
            ARM_BODY_LENGTH,
            ARM_BODY_WIDTH,
            ARM_BODY_HEIGHT,
        )
        .translate((ARM_BODY_CENTER_X, 0.0, 0.0))
    )
    tip_pad = (
        cq.Workplane("XY")
        .box(
            ARM_TIP_PAD_LENGTH,
            ARM_TIP_PAD_WIDTH,
            ARM_TIP_PAD_HEIGHT,
        )
        .translate((ARM_TIP_PAD_CENTER_X, 0.0, 0.0))
    )
    tip = cq.Workplane("XY").sphere(ARM_TIP_RADIUS).translate((ARM_TIP_X, 0.0, 0.0))

    return barrel.union(shoulder).union(beam).union(tip_pad).union(tip)
def _add_branch_part(model: ArticulatedObject, mesh, name: str):
    branch = model.part(name)
    branch.visual(mesh, material="arm_blue")





    branch.inertial = Inertial.from_geometry(
        Box((ARM_INERTIAL_LENGTH, ARM_INERTIAL_WIDTH, ARM_INERTIAL_HEIGHT)),
        mass=0.24,
        origin=Origin(xyz=(ARM_INERTIAL_CENTER_X, 0.0, 0.0)),
    )
    return branch
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="rotary_tree_mechanism", assets=ASSETS)

    model.material("hub_gray", rgba=(0.58, 0.60, 0.63, 1.0))
    model.material("arm_blue", rgba=(0.23, 0.45, 0.72, 1.0))

    hub_mesh = mesh_from_cadquery(_build_hub_shape(), "rotary_tree_hub.obj", assets=ASSETS)
    arm_mesh = mesh_from_cadquery(_build_arm_shape(), "rotary_tree_arm.obj", assets=ASSETS)

    hub = model.part("hub")
    hub.visual(hub_mesh, material="hub_gray")


    for angle in BRANCH_ANGLES:
        pass
    hub.inertial = Inertial.from_geometry(
        Cylinder(radius=HUB_RADIUS, length=HUB_HEIGHT),
        mass=1.15,
    )

    for name, angle in zip(BRANCH_NAMES, BRANCH_ANGLES):
        branch = _add_branch_part(model, arm_mesh, name)
        model.articulation(
            f"hub_to_{name}",
            ArticulationType.REVOLUTE,
            parent=hub,
            child=branch,
            origin=Origin(
                xyz=(JOINT_RADIUS * cos(angle), JOINT_RADIUS * sin(angle), 0.0),
                rpy=(0.0, 0.0, angle),
            ),
            axis=(0.0, -1.0, 0.0),
            motion_limits=ARM_LIMITS,
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
