# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cantilever_articulated_arm, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cantilever_articulated_arm

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
PEDESTAL_TOP_Z = 0.17
SHOULDER_OFFSET = (0.12, 0.0, 0.08)
ELBOW_X = 0.40
WRIST_X = 0.34
YAW_LIMIT = 1.6
SHOULDER_LOWER = -0.25
SHOULDER_UPPER = 1.05
ELBOW_LOWER = -0.15
ELBOW_UPPER = 1.55
WRIST_YAW_LIMIT = 1.15
def _filleted_box(
    size: tuple[float, float, float],
    xyz: tuple[float, float, float],
    radius: float,
) -> cq.Workplane:
    shape = cq.Workplane("XY").box(*size)
    if radius > 0.0:
        shape = shape.edges("|Z").fillet(radius)
    return shape.translate(xyz)
def _mesh_visual(part, shape: cq.Workplane, filename: str, material: str) -> None:
    part.visual(mesh_from_cadquery(shape, filename, assets=ASSETS), material=material)
def _box_collision(
    part,
    size: tuple[float, float, float],
    xyz: tuple[float, float, float],
) -> None:
    pass
def _pedestal_shape() -> cq.Workplane:
    foot = _filleted_box((0.30, 0.26, 0.05), (0.0, 0.0, -0.145), 0.010)
    column = _filleted_box((0.22, 0.18, 0.25), (0.0, 0.0, -0.005), 0.012)
    top = _filleted_box((0.16, 0.16, 0.05), (0.0, 0.0, 0.145), 0.008)
    return foot.union(column).union(top)
def _turret_shape() -> cq.Workplane:
    base = _filleted_box((0.18, 0.20, 0.08), (0.0, 0.0, 0.04), 0.008)
    top = _filleted_box((0.12, 0.12, 0.04), (0.0, 0.0, 0.10), 0.006)
    shoulder_cheek = _filleted_box((0.06, 0.14, 0.12), (0.10, 0.0, 0.08), 0.006)
    return base.union(top).union(shoulder_cheek)
def _upper_arm_shape() -> cq.Workplane:
    shoulder_housing = _filleted_box((0.10, 0.16, 0.16), (0.035, 0.0, 0.0), 0.007)
    beam = _filleted_box((0.34, 0.06, 0.06), (0.22, 0.0, 0.0), 0.005)
    top_rib = _filleted_box((0.26, 0.03, 0.03), (0.20, 0.0, 0.045), 0.003)
    elbow_housing = _filleted_box((0.10, 0.12, 0.12), (ELBOW_X, 0.0, 0.0), 0.006)
    return shoulder_housing.union(beam).union(top_rib).union(elbow_housing)
def _forearm_shape() -> cq.Workplane:
    elbow_housing = _filleted_box((0.09, 0.13, 0.13), (0.035, 0.0, 0.0), 0.006)
    beam = _filleted_box((0.28, 0.05, 0.05), (0.18, 0.0, 0.0), 0.004)
    lower_strake = _filleted_box((0.20, 0.03, 0.03), (0.17, 0.0, -0.040), 0.003)
    wrist_housing = _filleted_box((0.08, 0.10, 0.10), (0.31, 0.0, 0.0), 0.005)
    return elbow_housing.union(beam).union(lower_strake).union(wrist_housing)
def _tool_head_shape() -> cq.Workplane:
    wrist_housing = _filleted_box((0.08, 0.10, 0.10), (0.03, 0.0, 0.0), 0.005)
    beam = _filleted_box((0.14, 0.04, 0.04), (0.10, 0.0, 0.0), 0.003)
    jaw_upper = _filleted_box((0.05, 0.02, 0.08), (0.17, 0.035, 0.0), 0.002)
    jaw_lower = _filleted_box((0.05, 0.02, 0.08), (0.17, -0.035, 0.0), 0.002)
    return wrist_housing.union(beam).union(jaw_upper).union(jaw_lower)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="overhung_mechanical_arm", assets=ASSETS)

    model.material("pedestal_gray", rgba=(0.32, 0.34, 0.37, 1.0))
    model.material("actuator_dark", rgba=(0.15, 0.16, 0.18, 1.0))
    model.material("beam_blue", rgba=(0.18, 0.34, 0.68, 1.0))
    model.material("tool_orange", rgba=(0.92, 0.48, 0.14, 1.0))

    pedestal = model.part("pedestal")
    _mesh_visual(pedestal, _pedestal_shape(), "pedestal.obj", "pedestal_gray")
    _box_collision(pedestal, (0.30, 0.26, 0.05), (0.0, 0.0, -0.145))
    _box_collision(pedestal, (0.22, 0.18, 0.25), (0.0, 0.0, -0.005))
    _box_collision(pedestal, (0.16, 0.16, 0.05), (0.0, 0.0, 0.145))
    pedestal.inertial = Inertial.from_geometry(
        Box((0.26, 0.22, 0.30)),
        mass=18.0,
    )

    yaw_housing = model.part("yaw_housing")
    _mesh_visual(yaw_housing, _turret_shape(), "yaw_housing.obj", "actuator_dark")
    _box_collision(yaw_housing, (0.18, 0.20, 0.08), (0.0, 0.0, 0.04))
    _box_collision(yaw_housing, (0.12, 0.12, 0.04), (0.0, 0.0, 0.10))
    _box_collision(yaw_housing, (0.06, 0.12, 0.10), (0.10, 0.0, 0.08))
    yaw_housing.inertial = Inertial.from_geometry(
        Box((0.18, 0.20, 0.13)),
        mass=4.2,
        origin=Origin(xyz=(0.01, 0.0, 0.065)),
    )

    upper_arm = model.part("upper_arm")
    _mesh_visual(upper_arm, _upper_arm_shape(), "upper_arm.obj", "beam_blue")
    _box_collision(upper_arm, (0.12, 0.14, 0.14), (0.04, 0.0, 0.0))
    _box_collision(upper_arm, (0.30, 0.05, 0.05), (0.22, 0.0, 0.0))
    _box_collision(upper_arm, (0.10, 0.10, 0.10), (0.36, 0.0, 0.0))
    upper_arm.inertial = Inertial.from_geometry(
        Box((0.42, 0.12, 0.12)),
        mass=4.8,
        origin=Origin(xyz=(0.21, 0.0, 0.0)),
    )

    forearm = model.part("forearm")
    _mesh_visual(forearm, _forearm_shape(), "forearm.obj", "beam_blue")
    _box_collision(forearm, (0.11, 0.11, 0.11), (0.045, 0.0, 0.0))
    _box_collision(forearm, (0.24, 0.05, 0.05), (0.17, 0.0, 0.0))
    _box_collision(forearm, (0.07, 0.09, 0.09), (0.315, 0.0, 0.0))
    forearm.inertial = Inertial.from_geometry(
        Box((0.34, 0.11, 0.10)),
        mass=3.2,
        origin=Origin(xyz=(0.17, 0.0, -0.005)),
    )

    tool_head = model.part("tool_head")
    _mesh_visual(tool_head, _tool_head_shape(), "tool_head.obj", "tool_orange")
    _box_collision(tool_head, (0.10, 0.08, 0.08), (0.04, 0.0, 0.0))
    _box_collision(tool_head, (0.12, 0.04, 0.04), (0.10, 0.0, 0.0))
    _box_collision(tool_head, (0.05, 0.10, 0.08), (0.17, 0.0, 0.0))
    tool_head.inertial = Inertial.from_geometry(
        Box((0.22, 0.10, 0.08)),
        mass=1.1,
        origin=Origin(xyz=(0.11, 0.0, 0.0)),
    )

    model.articulation(
        "pedestal_to_turret",
        ArticulationType.REVOLUTE,
        parent=pedestal,
        child=yaw_housing,
        origin=Origin(xyz=(0.0, 0.0, PEDESTAL_TOP_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            lower=-YAW_LIMIT,
            upper=YAW_LIMIT,
            effort=60.0,
            velocity=1.5,
        ),
    )
    model.articulation(
        "turret_to_upper_arm",
        ArticulationType.REVOLUTE,
        parent=yaw_housing,
        child=upper_arm,
        origin=Origin(xyz=SHOULDER_OFFSET),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=SHOULDER_LOWER,
            upper=SHOULDER_UPPER,
            effort=45.0,
            velocity=1.5,
        ),
    )
    model.articulation(
        "upper_arm_to_forearm",
        ArticulationType.REVOLUTE,
        parent=upper_arm,
        child=forearm,
        origin=Origin(xyz=(ELBOW_X, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=ELBOW_LOWER,
            upper=ELBOW_UPPER,
            effort=35.0,
            velocity=1.8,
        ),
    )
    model.articulation(
        "forearm_to_tool",
        ArticulationType.REVOLUTE,
        parent=forearm,
        child=tool_head,
        origin=Origin(xyz=(WRIST_X, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            lower=-WRIST_YAW_LIMIT,
            upper=WRIST_YAW_LIMIT,
            effort=15.0,
            velocity=2.5,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
