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
import math
import cadquery as cq
ASSETS = AssetContext.from_script(__file__)
BASE_RADIUS = 0.078
BASE_THICKNESS = 0.018
MAST_RADIUS = 0.015
MAST_HEIGHT = 0.285
HUB_BODY_LENGTH = 0.050
HUB_BODY_WIDTH = 0.032
HUB_BODY_HEIGHT = 0.018
HUB_BODY_INNER_X = MAST_RADIUS + 0.006
HUB_COLLAR_OUTER_RADIUS = MAST_RADIUS + 0.009
HUB_COLLAR_INNER_RADIUS = MAST_RADIUS - 0.0008
HUB_CLAMP_GAP = 0.006
PIVOT_X = 0.055
PIVOT_BOSS_RADIUS = 0.013
PIVOT_BOSS_HEIGHT = 0.008
ARM_COLLAR_RADIUS = 0.013
ARM_COLLAR_HEIGHT = 0.008
ARM_BEAM_WIDTH = 0.018
ARM_BEAM_HEIGHT = 0.008
ARM_SWEEP = math.radians(60.0)
HUB_SPECS = (
    {
        "hub": "hub_lower",
        "arm": "arm_lower",
        "joint": "hub_lower_to_arm_lower",
        "height": 0.080,
        "yaw_deg": 0.0,
        "length": 0.112,
        "style": "pad_round",
    },
    {
        "hub": "hub_middle",
        "arm": "arm_middle",
        "joint": "hub_middle_to_arm_middle",
        "height": 0.155,
        "yaw_deg": 128.0,
        "length": 0.098,
        "style": "pad_square",
    },
    {
        "hub": "hub_upper",
        "arm": "arm_upper",
        "joint": "hub_upper_to_arm_upper",
        "height": 0.230,
        "yaw_deg": 246.0,
        "length": 0.106,
        "style": "fork",
    },
)
def _frame_shape() -> cq.Workplane:
    base = cq.Workplane("XY").circle(BASE_RADIUS).extrude(BASE_THICKNESS)
    base = (
        base.faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .pushPoints(
            [
                (0.050, 0.0),
                (-0.025, 0.043),
                (-0.025, -0.043),
            ]
        )
        .hole(0.010)
    )

    mast = (
        cq.Workplane("XY")
        .circle(MAST_RADIUS)
        .extrude(MAST_HEIGHT)
        .translate((0.0, 0.0, BASE_THICKNESS))
    )
    top_cap = (
        cq.Workplane("XY")
        .circle(MAST_RADIUS * 1.18)
        .extrude(0.010)
        .translate((0.0, 0.0, BASE_THICKNESS + MAST_HEIGHT))
    )

    rib_seed = (
        cq.Workplane("XY")
        .box(0.042, 0.010, 0.050, centered=(False, True, False))
        .translate((0.006, 0.0, BASE_THICKNESS))
    )
    ribs = rib_seed
    for angle_deg in (120.0, 240.0):
        ribs = ribs.union(rib_seed.rotate((0, 0, 0), (0, 0, 1), angle_deg))

    return base.union(mast).union(top_cap).union(ribs)
def _hub_shape() -> cq.Workplane:
    collar = (
        cq.Workplane("XY")
        .circle(HUB_COLLAR_OUTER_RADIUS)
        .circle(HUB_COLLAR_INNER_RADIUS)
        .extrude(HUB_BODY_HEIGHT)
    )
    clamp_relief = (
        cq.Workplane("XY")
        .box(HUB_CLAMP_GAP, HUB_COLLAR_OUTER_RADIUS * 2.4, HUB_BODY_HEIGHT + 0.002, centered=(False, True, False))
        .translate((-HUB_CLAMP_GAP, 0.0, -0.001))
    )
    collar = collar.cut(clamp_relief)
    body = (
        cq.Workplane("XY")
        .box(HUB_BODY_LENGTH, HUB_BODY_WIDTH, HUB_BODY_HEIGHT, centered=(False, True, False))
        .translate((HUB_BODY_INNER_X, 0.0, 0.0))
    )
    body = body.faces(">X").edges("|Z").fillet(0.004)

    boss = (
        cq.Workplane("XY")
        .circle(PIVOT_BOSS_RADIUS)
        .extrude(PIVOT_BOSS_HEIGHT)
        .translate((PIVOT_X, 0.0, HUB_BODY_HEIGHT))
    )
    return collar.union(body).union(boss)
def _arm_shape(length: float, style: str) -> cq.Workplane:
    collar = cq.Workplane("XY").circle(ARM_COLLAR_RADIUS).extrude(ARM_COLLAR_HEIGHT)
    beam_length = length - 0.024
    beam = (
        cq.Workplane("XY")
        .box(beam_length, ARM_BEAM_WIDTH, ARM_BEAM_HEIGHT, centered=(False, True, False))
        .translate((ARM_COLLAR_RADIUS * 0.45, 0.0, 0.0))
    )

    arm = collar.union(beam)

    if style == "pad_round":
        tip = (
            cq.Workplane("XY")
            .circle(0.014)
            .extrude(0.006)
            .translate((length, 0.0, 0.001))
        )
        arm = arm.union(tip)
    elif style == "pad_square":
        tip = (
            cq.Workplane("XY")
            .box(0.024, 0.024, 0.006, centered=(True, True, False))
            .translate((length, 0.0, 0.001))
        )
        arm = arm.union(tip)
    elif style == "fork":
        fork_body = (
            cq.Workplane("XY")
            .box(0.028, 0.024, ARM_BEAM_HEIGHT, centered=(False, True, False))
            .translate((length - 0.020, 0.0, 0.0))
        )
        slot = (
            cq.Workplane("XY")
            .box(0.022, 0.010, ARM_BEAM_HEIGHT + 0.002, centered=(False, True, False))
            .translate((length - 0.014, 0.0, -0.001))
        )
        arm = arm.union(fork_body).cut(slot)

    return arm
def _arm_inertial_origin(length: float) -> Origin:
    return Origin(xyz=(length * 0.52, 0.0, ARM_BEAM_HEIGHT * 0.5))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="three_branch_rotary_fixture", assets=ASSETS)

    graphite = model.material("graphite", rgba=(0.22, 0.24, 0.27, 1.0))
    steel = model.material("steel", rgba=(0.58, 0.60, 0.63, 1.0))
    anodized = model.material("anodized_blue", rgba=(0.26, 0.35, 0.47, 1.0))
    rubber = model.material("rubber", rgba=(0.12, 0.12, 0.13, 1.0))

    frame = model.part("frame")
    frame.visual(
        mesh_from_cadquery(_frame_shape(), "frame_shell.obj", assets=ASSETS),
        name="frame_shell",
        material=graphite,
    )
    frame.inertial = Inertial.from_geometry(
        Box((BASE_RADIUS * 2.0, BASE_RADIUS * 2.0, BASE_THICKNESS + MAST_HEIGHT + 0.010)),
        mass=4.8,
        origin=Origin(xyz=(0.0, 0.0, (BASE_THICKNESS + MAST_HEIGHT + 0.010) * 0.5)),
    )

    for spec in HUB_SPECS:
        hub = model.part(spec["hub"])
        hub.visual(
            mesh_from_cadquery(_hub_shape(), f"{spec['hub']}_shell.obj", assets=ASSETS),
            name="hub_shell",
            material=steel,
        )
        hub.inertial = Inertial.from_geometry(
            Box((0.068, HUB_BODY_WIDTH, HUB_BODY_HEIGHT + PIVOT_BOSS_HEIGHT)),
            mass=0.62,
            origin=Origin(
                xyz=(
                    HUB_BODY_INNER_X + HUB_BODY_LENGTH * 0.45,
                    0.0,
                    (HUB_BODY_HEIGHT + PIVOT_BOSS_HEIGHT) * 0.5,
                )
            ),
        )

        arm = model.part(spec["arm"])
        arm_material = rubber if spec["style"] == "pad_round" else anodized
        arm.visual(
            mesh_from_cadquery(
                _arm_shape(spec["length"], spec["style"]),
                f"{spec['arm']}_shell.obj",
                assets=ASSETS,
            ),
            name="arm_shell",
            material=arm_material,
        )
        arm.inertial = Inertial.from_geometry(
            Box((spec["length"] + 0.020, 0.026, ARM_COLLAR_HEIGHT)),
            mass=0.34,
            origin=_arm_inertial_origin(spec["length"]),
        )

        model.articulation(
            f"frame_to_{spec['hub']}",
            ArticulationType.FIXED,
            parent=frame,
            child=hub,
            origin=Origin(
                xyz=(0.0, 0.0, spec["height"]),
                rpy=(0.0, 0.0, math.radians(spec["yaw_deg"])),
            ),
        )

        model.articulation(
            spec["joint"],
            ArticulationType.REVOLUTE,
            parent=hub,
            child=arm,
            origin=Origin(xyz=(PIVOT_X, 0.0, HUB_BODY_HEIGHT + PIVOT_BOSS_HEIGHT)),
            axis=(0.0, 0.0, 1.0),
            motion_limits=MotionLimits(
                effort=10.0,
                velocity=1.8,
                lower=-ARM_SWEEP,
                upper=ARM_SWEEP,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
