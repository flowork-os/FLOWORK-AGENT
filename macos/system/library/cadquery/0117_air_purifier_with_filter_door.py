# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_purifier_with_filter_door, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_purifier_with_filter_door

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
BODY_W = 0.220
BODY_D = 0.125
BODY_H = 0.390
WALL_T = 0.011
FRONT_WALL_T = 0.018
BASE_T = 0.020
PANEL_W = 0.198
PANEL_H = 0.308
PANEL_T = 0.006
PANEL_BOTTOM_Z = 0.036
PANEL_HINGE_Y = -(BODY_D / 2.0) - (PANEL_T / 2.0)
PANEL_HINGE_X = PANEL_W / 2.0
FILTER_W = 0.182
FILTER_D = 0.074
FILTER_H = 0.286
FILTER_BOTTOM_Z = 0.048
FILTER_REAR_Y = -(BODY_D / 2.0) + 0.006
FILTER_TRAVEL = 0.042
TRAY_W = 0.078
TRAY_D = 0.054
TRAY_H = 0.012
TRAY_HINGE_Y = -0.006
OUTLET_W = 0.118
def _box_from_ranges(
    sx: float,
    sy: float,
    sz: float,
    *,
    cx: float = 0.0,
    cy: float = 0.0,
    z0: float = 0.0,
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(sx, sy, sz, centered=(True, True, False))
        .translate((cx, cy, z0))
    )
def _build_rear_panel_shape() -> cq.Workplane:
    panel = (
        cq.Workplane("XY")
        .box(PANEL_W, PANEL_T, PANEL_H, centered=(False, True, False))
        .translate((-PANEL_W, 0.0, 0.0))
    )

    slot_w = PANEL_W - 0.050
    slot_h = 0.010
    for idx in range(7):
        z = 0.052 + (idx * 0.033)
        slot = (
            cq.Workplane("XY")
            .box(slot_w, 0.012, slot_h, centered=(True, True, False))
            .translate((-(PANEL_W * 0.54), 0.0, z))
        )
        panel = panel.cut(slot)

    latch_finger = (
        cq.Workplane("XZ")
        .center(-PANEL_W + 0.011, PANEL_H * 0.56)
        .circle(0.008)
        .extrude(0.010, both=True)
    )
    panel = panel.cut(latch_finger)

    hinge_spine = (
        cq.Workplane("XY")
        .circle(0.003)
        .extrude(PANEL_H)
        .translate((0.0, 0.0, 0.0))
    )
    panel = panel.union(hinge_spine)

    return panel
def _build_filter_shape() -> cq.Workplane:
    filter_body = _box_from_ranges(
        FILTER_W,
        FILTER_D,
        FILTER_H,
        z0=0.0,
        cy=FILTER_D / 2.0,
    )

    media_recess = _box_from_ranges(
        FILTER_W - 0.020,
        FILTER_D - 0.010,
        FILTER_H - 0.020,
        z0=0.006,
        cy=(FILTER_D - 0.010) / 2.0,
    )
    filter_body = filter_body.cut(media_recess)

    rib_depth = FILTER_D - 0.014
    for idx in range(12):
        x = -0.066 + (idx * 0.012)
        rib = _box_from_ranges(
            0.005,
            rib_depth,
            FILTER_H - 0.032,
            cx=x,
            cy=0.004 + (rib_depth / 2.0),
            z0=0.016,
        )
        filter_body = filter_body.union(rib)

    top_grip = _box_from_ranges(
        0.040,
        0.010,
        0.010,
        cy=0.005,
        z0=FILTER_H - 0.002,
    )
    filter_body = filter_body.union(top_grip)

    return filter_body
def _build_tray_shape() -> cq.Workplane:
    tray = cq.Workplane("XY").box(TRAY_W, TRAY_D, TRAY_H, centered=(True, False, False))

    pocket = _box_from_ranges(
        TRAY_W - 0.012,
        TRAY_D - 0.010,
        TRAY_H - 0.003,
        cy=(TRAY_D - 0.010) / 2.0 + 0.002,
        z0=0.003,
    )
    tray = tray.cut(pocket)

    front_lip = _box_from_ranges(
        0.030,
        0.004,
        0.004,
        cy=TRAY_D - 0.002,
        z0=TRAY_H - 0.004,
    )
    tray = tray.union(front_lip)

    return tray
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="desktop_air_purifier")

    shell_white = model.material("shell_white", rgba=(0.95, 0.96, 0.94, 1.0))
    intake_gray = model.material("intake_gray", rgba=(0.83, 0.84, 0.80, 1.0))
    filter_charcoal = model.material("filter_charcoal", rgba=(0.24, 0.26, 0.28, 1.0))
    tray_dark = model.material("tray_dark", rgba=(0.18, 0.19, 0.21, 1.0))

    body = model.part("body")
    body.visual(
        Box((BODY_W, FRONT_WALL_T, BODY_H)),
        origin=Origin(xyz=(0.0, (BODY_D / 2.0) - (FRONT_WALL_T / 2.0), BODY_H / 2.0)),
        material=shell_white,
        name="front_shell",
    )
    body.visual(
        Box((WALL_T, BODY_D, BODY_H)),
        origin=Origin(xyz=((BODY_W / 2.0) - (WALL_T / 2.0), 0.0, BODY_H / 2.0)),
        material=shell_white,
        name="side_shell_0",
    )
    body.visual(
        Box((WALL_T, BODY_D, BODY_H)),
        origin=Origin(xyz=(-(BODY_W / 2.0) + (WALL_T / 2.0), 0.0, BODY_H / 2.0)),
        material=shell_white,
        name="side_shell_1",
    )
    body.visual(
        Box((BODY_W, BODY_D, BASE_T)),
        origin=Origin(xyz=(0.0, 0.0, BASE_T / 2.0)),
        material=shell_white,
        name="bottom_shell",
    )
    body.visual(
        Box((BODY_W, 0.066, 0.014)),
        origin=Origin(xyz=(0.0, -0.0295, BODY_H - 0.007)),
        material=shell_white,
        name="top_rear_deck",
    )
    body.visual(
        Box(((BODY_W - OUTLET_W) / 2.0, 0.046, 0.014)),
        origin=Origin(xyz=(0.0845, 0.027, BODY_H - 0.007)),
        material=shell_white,
        name="top_shoulder_0",
    )
    body.visual(
        Box(((BODY_W - OUTLET_W) / 2.0, 0.046, 0.014)),
        origin=Origin(xyz=(-0.0845, 0.027, BODY_H - 0.007)),
        material=shell_white,
        name="top_shoulder_1",
    )
    body.visual(
        Box((BODY_W, 0.013, 0.014)),
        origin=Origin(xyz=(0.0, 0.056, BODY_H - 0.007)),
        material=shell_white,
        name="top_front_lip",
    )
    body.visual(
        Box((PANEL_W, 0.006, PANEL_BOTTOM_Z)),
        origin=Origin(xyz=(0.0, -(BODY_D / 2.0) + 0.003, PANEL_BOTTOM_Z / 2.0)),
        material=shell_white,
        name="rear_frame_bottom",
    )
    body.visual(
        Box((PANEL_W, 0.006, BODY_H - (PANEL_BOTTOM_Z + PANEL_H))),
        origin=Origin(
            xyz=(
                0.0,
                -(BODY_D / 2.0) + 0.003,
                PANEL_BOTTOM_Z + PANEL_H + ((BODY_H - (PANEL_BOTTOM_Z + PANEL_H)) / 2.0),
            )
        ),
        material=shell_white,
        name="rear_frame_top",
    )
    body.visual(
        Box(((BODY_W - PANEL_W) / 2.0, 0.006, PANEL_H)),
        origin=Origin(
            xyz=(
                PANEL_HINGE_X + ((BODY_W - PANEL_W) / 4.0),
                -(BODY_D / 2.0) + 0.003,
                PANEL_BOTTOM_Z + (PANEL_H / 2.0),
            )
        ),
        material=shell_white,
        name="rear_frame_hinge",
    )
    body.visual(
        Box(((BODY_W - PANEL_W) / 2.0, 0.006, PANEL_H)),
        origin=Origin(
            xyz=(
                -PANEL_HINGE_X - ((BODY_W - PANEL_W) / 4.0),
                -(BODY_D / 2.0) + 0.003,
                PANEL_BOTTOM_Z + (PANEL_H / 2.0),
            )
        ),
        material=shell_white,
        name="rear_frame_latch",
    )
    body.visual(
        Box((0.008, 0.038, 0.004)),
        origin=Origin(xyz=(0.095, -0.036, 0.046)),
        material=shell_white,
        name="guide_0",
    )
    body.visual(
        Box((0.008, 0.038, 0.004)),
        origin=Origin(xyz=(-0.095, -0.036, 0.046)),
        material=shell_white,
        name="guide_1",
    )
    body.visual(
        Box((0.012, 0.010, PANEL_H)),
        origin=Origin(xyz=(0.104, -0.0575, PANEL_BOTTOM_Z + (PANEL_H / 2.0))),
        material=shell_white,
        name="hinge_boss",
    )
    body.visual(
        Box((0.010, 0.008, 0.055)),
        origin=Origin(xyz=(-0.102, -0.0585, PANEL_BOTTOM_Z + 0.1375)),
        material=shell_white,
        name="latch_boss",
    )

    rear_panel = model.part("rear_panel")
    rear_panel.visual(
        mesh_from_cadquery(_build_rear_panel_shape(), "rear_panel"),
        material=intake_gray,
        name="rear_cover",
    )

    cassette_filter = model.part("cassette_filter")
    cassette_filter.visual(
        mesh_from_cadquery(_build_filter_shape(), "cassette_filter"),
        material=filter_charcoal,
        name="cassette",
    )

    fragrance_tray = model.part("fragrance_tray")
    fragrance_tray.visual(
        mesh_from_cadquery(_build_tray_shape(), "fragrance_tray"),
        material=tray_dark,
        name="tray",
    )

    model.articulation(
        "rear_panel_hinge",
        ArticulationType.REVOLUTE,
        parent=body,
        child=rear_panel,
        origin=Origin(xyz=(PANEL_HINGE_X, PANEL_HINGE_Y, PANEL_BOTTOM_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=5.0,
            velocity=2.0,
            lower=0.0,
            upper=math.radians(120.0),
        ),
    )

    model.articulation(
        "filter_slide",
        ArticulationType.PRISMATIC,
        parent=body,
        child=cassette_filter,
        origin=Origin(xyz=(0.0, FILTER_REAR_Y, FILTER_BOTTOM_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=0.10,
            lower=0.0,
            upper=FILTER_TRAVEL,
        ),
    )

    model.articulation(
        "tray_hinge",
        ArticulationType.REVOLUTE,
        parent=body,
        child=fragrance_tray,
        origin=Origin(xyz=(0.0, TRAY_HINGE_Y, BODY_H)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=1.5,
            velocity=2.5,
            lower=0.0,
            upper=math.radians(95.0),
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
