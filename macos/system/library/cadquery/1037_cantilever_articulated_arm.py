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

# ===== model =====
from math import radians
import cadquery as cq
BASE_LENGTH = 0.28
BASE_WIDTH = 0.20
BASE_HEIGHT = 0.035
COUNTER_LENGTH = 0.12
COUNTER_WIDTH = 0.18
COUNTER_HEIGHT = 0.095
COLUMN_LENGTH = 0.10
COLUMN_WIDTH = 0.11
COLUMN_HEIGHT = 0.48
BEAM_WIDTH = 0.11
BEAM_HEIGHT = 0.08
SHOULDER_X = 0.14
SHOULDER_Z = 0.58
SHOULDER_LINK_LENGTH = 0.44
ELBOW_LINK_LENGTH = 0.36
WRIST_LINK_LENGTH = 0.20
SUPPORT_GAP = 0.028
STAGE_2_GAP = 0.026
STAGE_3_GAP = 0.024
EAR_THICKNESS = 0.014
SHOULDER_LIMITS = (-0.60, 0.95)
ELBOW_LIMITS = (-1.25, 1.20)
WRIST_LIMITS = (-0.95, 1.05)
def _box(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(center)
def _xz_profile_prism(points: list[tuple[float, float]], width: float) -> cq.Workplane:
    return cq.Workplane("XZ").polyline(points).close().extrude(width / 2.0, both=True)
def _underslung_link_shape(
    *,
    length: float,
    body_width: float,
    body_height: float,
    root_lug_width: float,
    child_gap: float,
) -> cq.Workplane:
    body_top = -0.034
    body_z = body_top - (body_height / 2.0)
    web_width = max(body_width * 0.72, root_lug_width + 0.012)
    child_ear_y = (child_gap / 2.0) + (EAR_THICKNESS / 2.0)
    root_block_length = 0.024
    neck_length = 0.060
    body_start = 0.076
    body_length = max(length - 0.190, 0.150)
    distal_block_length = 0.080
    distal_block_center = length - 0.064
    fork_ear_length = 0.032

    shape = _box(
        (root_block_length, root_lug_width, 0.050),
        (root_block_length / 2.0, 0.0, 0.0),
    )
    shape = shape.union(
        _box(
            (neck_length, web_width, 0.088),
            (0.052, 0.0, -0.044),
        )
    )
    shape = shape.union(
        _box(
            (body_length, body_width, body_height),
            (body_start + (body_length / 2.0), 0.0, body_z),
        )
    )
    shape = shape.union(
        _box(
            (0.135, body_width * 0.76, 0.020),
            (body_start + 0.055, 0.0, -0.020),
        )
    )
    shape = shape.union(
        _box(
            (distal_block_length, web_width, 0.074),
            (distal_block_center, 0.0, -0.038),
        )
    )
    shape = shape.union(
        _box(
            (0.024, web_width * 0.82, 0.046),
            (length - 0.108, 0.0, -0.034),
        )
    )

    for y_pos in (-child_ear_y, child_ear_y):
        shape = shape.union(
            _box(
                (fork_ear_length, EAR_THICKNESS, 0.052),
                (length - (fork_ear_length / 2.0), y_pos, 0.0),
            )
        )

    return shape
def _wrist_stage_shape(
    *,
    length: float,
    body_width: float,
    body_height: float,
    root_lug_width: float,
) -> cq.Workplane:
    body_top = -0.030
    body_z = body_top - (body_height / 2.0)
    web_width = max(body_width * 0.78, root_lug_width + 0.012)
    root_block_length = 0.024

    shape = _box(
        (root_block_length, root_lug_width, 0.048),
        (root_block_length / 2.0, 0.0, 0.0),
    )
    shape = shape.union(_box((0.072, web_width, 0.084), (0.050, 0.0, -0.042)))
    shape = shape.union(
        _box(
            (length - 0.030, body_width, body_height),
            (0.036 + ((length - 0.030) / 2.0), 0.0, body_z),
        )
    )
    shape = shape.union(_box((0.060, web_width, 0.066), (length - 0.020, 0.0, -0.034)))
    shape = shape.union(_box((0.068, body_width * 0.84, 0.022), (length + 0.004, 0.0, -0.030)))
    shape = shape.union(_box((0.022, body_width * 0.80, 0.092), (length + 0.018, 0.0, -0.012)))
    shape = shape.union(_box((0.040, body_width * 0.54, 0.046), (length + 0.048, 0.0, -0.022)))
    return shape
def _support_frame_shape() -> cq.Workplane:
    beam_center_x = -0.040
    beam_center_z = 0.65
    support_ear_y = (SUPPORT_GAP / 2.0) + (EAR_THICKNESS / 2.0)

    shape = _box((BASE_LENGTH, BASE_WIDTH, BASE_HEIGHT), (-0.045, 0.0, BASE_HEIGHT / 2.0))
    shape = shape.union(
        _box(
            (COUNTER_LENGTH, COUNTER_WIDTH, COUNTER_HEIGHT),
            (-0.115, 0.0, BASE_HEIGHT + COUNTER_HEIGHT / 2.0),
        )
    )
    shape = shape.union(
        _box(
            (COLUMN_LENGTH, COLUMN_WIDTH, COLUMN_HEIGHT),
            (-0.080, 0.0, BASE_HEIGHT + (COLUMN_HEIGHT / 2.0)),
        )
    )
    shape = shape.union(_box((0.240, BEAM_WIDTH, BEAM_HEIGHT), (beam_center_x, 0.0, beam_center_z)))

    brace = _xz_profile_prism(
        [
            (-0.120, 0.295),
            (-0.015, 0.295),
            (0.110, 0.610),
            (0.015, 0.610),
        ],
        0.062,
    )
    shape = shape.union(brace)

    shape = shape.union(_box((0.034, 0.050, 0.092), (0.082, 0.0, 0.604)))
    shape = shape.union(_box((0.078, SUPPORT_GAP + (2.0 * EAR_THICKNESS), 0.020), (0.101, 0.0, 0.620)))
    for y_pos in (-support_ear_y, support_ear_y):
        shape = shape.union(_box((0.032, EAR_THICKNESS, 0.056), (SHOULDER_X - 0.016, y_pos, SHOULDER_Z)))

    shape = shape.union(_box((0.110, 0.070, 0.030), (0.035, 0.0, beam_center_z - 0.026)))
    return shape
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="underslung_cantilever_arm")

    model.material("support_graphite", rgba=(0.20, 0.21, 0.23, 1.0))
    model.material("arm_aluminum", rgba=(0.73, 0.75, 0.78, 1.0))
    model.material("wrist_gray", rgba=(0.36, 0.38, 0.41, 1.0))

    support_frame = model.part("support_frame")
    support_frame.visual(
        mesh_from_cadquery(_support_frame_shape(), "support_frame"),
        material="support_graphite",
        name="support_shell",
    )
    support_frame.inertial = Inertial.from_geometry(
        Box((0.40, 0.22, 0.68)),
        mass=16.0,
        origin=Origin(xyz=(-0.025, 0.0, 0.33)),
    )

    shoulder_link = model.part("shoulder_link")
    shoulder_link.visual(
        mesh_from_cadquery(
            _underslung_link_shape(
                length=SHOULDER_LINK_LENGTH,
                body_width=0.072,
                body_height=0.074,
                root_lug_width=SUPPORT_GAP,
                child_gap=STAGE_2_GAP,
            ),
            "shoulder_link",
        ),
        material="arm_aluminum",
        name="shoulder_shell",
    )
    shoulder_link.inertial = Inertial.from_geometry(
        Box((SHOULDER_LINK_LENGTH, 0.09, 0.15)),
        mass=4.2,
        origin=Origin(xyz=(SHOULDER_LINK_LENGTH * 0.55, 0.0, -0.052)),
    )

    elbow_link = model.part("elbow_link")
    elbow_link.visual(
        mesh_from_cadquery(
            _underslung_link_shape(
                length=ELBOW_LINK_LENGTH,
                body_width=0.066,
                body_height=0.068,
                root_lug_width=STAGE_2_GAP,
                child_gap=STAGE_3_GAP,
            ),
            "elbow_link",
        ),
        material="arm_aluminum",
        name="elbow_shell",
    )
    elbow_link.inertial = Inertial.from_geometry(
        Box((ELBOW_LINK_LENGTH, 0.082, 0.14)),
        mass=3.1,
        origin=Origin(xyz=(ELBOW_LINK_LENGTH * 0.54, 0.0, -0.050)),
    )

    wrist_link = model.part("wrist_link")
    wrist_link.visual(
        mesh_from_cadquery(
            _wrist_stage_shape(
                length=WRIST_LINK_LENGTH,
                body_width=0.056,
                body_height=0.062,
                root_lug_width=STAGE_3_GAP,
            ),
            "wrist_link",
        ),
        material="wrist_gray",
        name="wrist_shell",
    )
    wrist_link.inertial = Inertial.from_geometry(
        Box((WRIST_LINK_LENGTH + 0.08, 0.070, 0.13)),
        mass=1.8,
        origin=Origin(xyz=(WRIST_LINK_LENGTH * 0.62, 0.0, -0.040)),
    )

    model.articulation(
        "shoulder_joint",
        ArticulationType.REVOLUTE,
        parent=support_frame,
        child=shoulder_link,
        origin=Origin(xyz=(SHOULDER_X, 0.0, SHOULDER_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=90.0,
            velocity=radians(35.0),
            lower=SHOULDER_LIMITS[0],
            upper=SHOULDER_LIMITS[1],
        ),
    )
    model.articulation(
        "elbow_joint",
        ArticulationType.REVOLUTE,
        parent=shoulder_link,
        child=elbow_link,
        origin=Origin(xyz=(SHOULDER_LINK_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=70.0,
            velocity=radians(45.0),
            lower=ELBOW_LIMITS[0],
            upper=ELBOW_LIMITS[1],
        ),
    )
    model.articulation(
        "wrist_joint",
        ArticulationType.REVOLUTE,
        parent=elbow_link,
        child=wrist_link,
        origin=Origin(xyz=(ELBOW_LINK_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=35.0,
            velocity=radians(70.0),
            lower=WRIST_LIMITS[0],
            upper=WRIST_LIMITS[1],
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
