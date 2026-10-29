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
import cadquery as cq
BASE_LENGTH = 0.200
BASE_WIDTH = 0.140
BASE_THICKNESS = 0.018
BASE_HOLE_RADIUS = 0.0065
COLUMN_WIDTH = 0.075
COLUMN_DEPTH = 0.060
COLUMN_HEIGHT = 0.320
JOINT_GAP = 0.034
JOINT_PLATE_THICKNESS = 0.010
JOINT_OUTER_WIDTH = JOINT_GAP + 2.0 * JOINT_PLATE_THICKNESS
SHOULDER_AXIS_X = 0.092
SHOULDER_AXIS_Z = BASE_THICKNESS + 0.305
UPPER_ARM_LENGTH = 0.245
FOREARM_LENGTH = 0.185
SHOULDER_HUB_RADIUS = 0.019
ELBOW_HUB_RADIUS = 0.018
WRIST_HUB_RADIUS = 0.015
LUG_WIDTH = JOINT_GAP
def _y_axis_cylinder(radius: float, length: float) -> cq.Workplane:
    return cq.Workplane("XZ").circle(radius).extrude(length / 2.0, both=True)
def _forward_lug(hub_radius: float, *, tongue_length: float, height: float) -> cq.Workplane:
    hub = _y_axis_cylinder(hub_radius, LUG_WIDTH).translate((hub_radius, 0.0, 0.0))
    tongue = cq.Workplane("XY").box(
        tongue_length,
        LUG_WIDTH,
        height,
        centered=(False, True, True),
    )
    return hub.union(tongue)
def _clevis(
    *,
    axis_x: float,
    body_back: float,
    body_front: float,
    height: float,
    slot_back: float,
    slot_front: float,
    slot_height: float,
) -> cq.Workplane:
    body = cq.Workplane("XY").box(
        body_back + body_front,
        JOINT_OUTER_WIDTH,
        height,
        centered=(False, True, True),
    ).translate((axis_x - body_back, 0.0, 0.0))
    slot = cq.Workplane("XY").box(
        slot_back + slot_front,
        LUG_WIDTH,
        slot_height,
        centered=(False, True, True),
    ).translate((axis_x - slot_back, 0.0, 0.0))
    return body.cut(slot)
def _support_shape() -> cq.Workplane:
    base = (
        cq.Workplane("XY")
        .box(BASE_LENGTH, BASE_WIDTH, BASE_THICKNESS, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.004)
    )
    base_holes = (
        cq.Workplane("XY")
        .pushPoints(
            [
                (-0.068, -0.044),
                (-0.068, 0.044),
                (0.068, -0.044),
                (0.068, 0.044),
            ]
        )
        .circle(BASE_HOLE_RADIUS)
        .extrude(BASE_THICKNESS + 0.010)
    )
    base = base.cut(base_holes)

    column = (
        cq.Workplane("XY")
        .box(COLUMN_WIDTH, COLUMN_DEPTH, COLUMN_HEIGHT, centered=(True, True, False))
        .translate((0.0, 0.0, BASE_THICKNESS))
        .edges("|Z")
        .fillet(0.004)
    )

    cantilever_start = COLUMN_WIDTH / 2.0 - 0.002
    cantilever_end = SHOULDER_AXIS_X - 0.042
    cantilever = cq.Workplane("XY").box(
        cantilever_end - cantilever_start,
        0.044,
        0.046,
        centered=(False, True, False),
    ).translate((cantilever_start, 0.0, SHOULDER_AXIS_Z - 0.023))

    shoulder_clevis = _clevis(
        axis_x=SHOULDER_AXIS_X,
        body_back=0.044,
        body_front=0.0,
        height=0.054,
        slot_back=0.010,
        slot_front=0.020,
        slot_height=0.038,
    ).translate((0.0, 0.0, SHOULDER_AXIS_Z))

    gusset = (
        cq.Workplane("XZ")
        .polyline(
            [
                (COLUMN_WIDTH / 2.0 - 0.002, BASE_THICKNESS + 0.105),
                (COLUMN_WIDTH / 2.0 - 0.002, SHOULDER_AXIS_Z - 0.024),
                (SHOULDER_AXIS_X - 0.044, SHOULDER_AXIS_Z - 0.024),
                (SHOULDER_AXIS_X - 0.044, SHOULDER_AXIS_Z - 0.090),
            ]
        )
        .close()
        .extrude(0.024, both=True)
    )

    return (
        base.union(column)
        .union(cantilever)
        .union(shoulder_clevis)
        .union(gusset)
    )
def _shoulder_link_shape() -> cq.Workplane:
    proximal_lug = _forward_lug(
        SHOULDER_HUB_RADIUS,
        tongue_length=0.030,
        height=0.036,
    )
    beam = (
        cq.Workplane("XY")
        .box(UPPER_ARM_LENGTH - 0.080, 0.024, 0.032, centered=(False, True, True))
        .translate((0.030, 0.0, 0.0))
        .edges("|X")
        .fillet(0.006)
    )
    elbow_clevis = _clevis(
        axis_x=UPPER_ARM_LENGTH,
        body_back=0.050,
        body_front=0.0,
        height=0.046,
        slot_back=0.016,
        slot_front=0.018,
        slot_height=0.034,
    )
    return proximal_lug.union(beam).union(elbow_clevis)
def _elbow_link_shape() -> cq.Workplane:
    proximal_lug = _forward_lug(
        ELBOW_HUB_RADIUS,
        tongue_length=0.028,
        height=0.032,
    )
    beam = (
        cq.Workplane("XY")
        .box(FOREARM_LENGTH - 0.074, 0.022, 0.028, centered=(False, True, True))
        .translate((0.028, 0.0, 0.0))
        .edges("|X")
        .fillet(0.005)
    )
    distal_bridge = cq.Workplane("XY").box(
        0.014,
        0.022,
        0.026,
        centered=(False, True, True),
    ).translate((FOREARM_LENGTH - 0.058, 0.0, 0.0))
    wrist_clevis = _clevis(
        axis_x=FOREARM_LENGTH,
        body_back=0.044,
        body_front=0.0,
        height=0.040,
        slot_back=0.014,
        slot_front=0.016,
        slot_height=0.030,
    )
    return proximal_lug.union(beam).union(distal_bridge).union(wrist_clevis)
def _wrist_tool_shape() -> cq.Workplane:
    proximal_lug = _forward_lug(
        WRIST_HUB_RADIUS,
        tongue_length=0.026,
        height=0.024,
    )
    bridge = cq.Workplane("XY").box(
        0.024, 0.022, 0.020, centered=(False, True, True)
    ).translate((0.024, 0.0, 0.0))
    plate = (
        cq.Workplane("XY")
        .box(0.086, 0.072, 0.012, centered=(False, True, True))
        .translate((0.044, 0.0, 0.0))
        .edges("|Z")
        .fillet(0.004)
    )
    front_pad = cq.Workplane("XY").box(
        0.014, 0.040, 0.018, centered=(False, True, True)
    ).translate((0.116, 0.0, 0.0))
    tool = proximal_lug.union(bridge).union(plate).union(front_pad)

    fastener_holes = (
        cq.Workplane("XY")
        .pushPoints([(0.052, -0.020), (0.052, 0.020), (0.084, -0.020), (0.084, 0.020)])
        .circle(0.0055)
        .extrude(0.020, both=True)
    )
    return tool.cut(fastener_holes)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bench_tooling_cantilever_arm")

    model.material("powder_steel", rgba=(0.23, 0.25, 0.28, 1.0))
    model.material("machined_aluminum", rgba=(0.72, 0.74, 0.77, 1.0))
    model.material("oxide_black", rgba=(0.12, 0.13, 0.14, 1.0))

    support = model.part("support")
    support.visual(
        mesh_from_cadquery(_support_shape(), "support_column"),
        material="powder_steel",
        name="support_shell",
    )

    shoulder_link = model.part("shoulder_link")
    shoulder_link.visual(
        mesh_from_cadquery(_shoulder_link_shape(), "shoulder_link"),
        material="machined_aluminum",
        name="shoulder_shell",
    )

    elbow_link = model.part("elbow_link")
    elbow_link.visual(
        mesh_from_cadquery(_elbow_link_shape(), "elbow_link"),
        material="machined_aluminum",
        name="elbow_shell",
    )

    wrist_tool = model.part("wrist_tool")
    wrist_tool.visual(
        mesh_from_cadquery(_wrist_tool_shape(), "wrist_tool"),
        material="oxide_black",
        name="wrist_shell",
    )

    model.articulation(
        "support_to_shoulder",
        ArticulationType.REVOLUTE,
        parent=support,
        child=shoulder_link,
        origin=Origin(xyz=(SHOULDER_AXIS_X, 0.0, SHOULDER_AXIS_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=-0.45,
            upper=1.20,
            effort=80.0,
            velocity=1.2,
        ),
    )
    model.articulation(
        "shoulder_to_elbow",
        ArticulationType.REVOLUTE,
        parent=shoulder_link,
        child=elbow_link,
        origin=Origin(xyz=(UPPER_ARM_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=-1.10,
            upper=1.10,
            effort=55.0,
            velocity=1.4,
        ),
    )
    model.articulation(
        "elbow_to_wrist",
        ArticulationType.REVOLUTE,
        parent=elbow_link,
        child=wrist_tool,
        origin=Origin(xyz=(FOREARM_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=-0.90,
            upper=0.95,
            effort=20.0,
            velocity=1.8,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
