# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camcorder_with_flipout_screen, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camcorder_with_flipout_screen

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
BODY_LEN = 0.132
BODY_WIDTH = 0.058
BODY_HEIGHT = 0.074
LENS_BARREL_RADIUS = 0.0248
LENS_BARREL_LENGTH = 0.014
LENS_RING_RADIUS = 0.031
LENS_RING_INNER_RADIUS = 0.0266
LENS_RING_LENGTH = 0.012
MONITOR_LEN = 0.072
MONITOR_THICKNESS = 0.008
MONITOR_HEIGHT = 0.054
MONITOR_HINGE_RADIUS = 0.004
MONITOR_HINGE_X = -0.030
MONITOR_HINGE_Y = BODY_WIDTH * 0.5 + MONITOR_HINGE_RADIUS
MONITOR_HINGE_Z = -0.021
PORT_COVER_LEN = 0.034
PORT_COVER_THICKNESS = 0.0045
PORT_COVER_HEIGHT = 0.018
PORT_COVER_HINGE_RADIUS = 0.0025
PORT_COVER_HINGE_X = -0.010
PORT_COVER_HINGE_Y = BODY_WIDTH * 0.5 + PORT_COVER_HINGE_RADIUS
PORT_COVER_HINGE_Z = -0.031
def _body_shell_mesh():
    main_shell = (
        cq.Workplane("XY")
        .box(BODY_LEN, BODY_WIDTH, BODY_HEIGHT)
        .edges("|Z")
        .fillet(0.010)
    )
    battery_pack = (
        cq.Workplane("XY")
        .box(0.030, 0.046, 0.048)
        .edges("|Z")
        .fillet(0.006)
        .translate((-0.073, 0.0, 0.004))
    )
    handgrip_bulge = (
        cq.Workplane("XY")
        .box(0.086, 0.018, 0.056)
        .edges("|Z")
        .fillet(0.008)
        .translate((0.006, -0.038, -0.002))
    )
    top_ridge = (
        cq.Workplane("XY")
        .box(0.050, 0.018, 0.010)
        .edges("|Z")
        .fillet(0.003)
        .translate((0.016, -0.004, 0.037))
    )
    return mesh_from_cadquery(
        main_shell.union(battery_pack).union(handgrip_bulge).union(top_ridge),
        "camcorder_body_shell",
    )
def _lens_ring_mesh():
    base_ring = (
        cq.Workplane("YZ")
        .circle(LENS_RING_RADIUS)
        .circle(LENS_RING_INNER_RADIUS)
        .extrude(LENS_RING_LENGTH)
    )
    ridge_a = (
        cq.Workplane("YZ")
        .circle(LENS_RING_RADIUS + 0.0012)
        .circle(LENS_RING_INNER_RADIUS)
        .extrude(0.0015)
        .translate((0.0020, 0.0, 0.0))
    )
    ridge_b = (
        cq.Workplane("YZ")
        .circle(LENS_RING_RADIUS + 0.0012)
        .circle(LENS_RING_INNER_RADIUS)
        .extrude(0.0015)
        .translate((0.0085, 0.0, 0.0))
    )
    return mesh_from_cadquery(
        base_ring.union(ridge_a).union(ridge_b).translate((-LENS_RING_LENGTH * 0.5, 0.0, 0.0)),
        "camcorder_lens_ring",
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="compact_camcorder")

    body_finish = model.material("body_finish", rgba=(0.17, 0.18, 0.19, 1.0))
    trim_finish = model.material("trim_finish", rgba=(0.28, 0.29, 0.31, 1.0))
    grip_finish = model.material("grip_finish", rgba=(0.09, 0.09, 0.10, 1.0))
    lens_finish = model.material("lens_finish", rgba=(0.11, 0.11, 0.12, 1.0))
    ring_finish = model.material("ring_finish", rgba=(0.40, 0.41, 0.43, 1.0))
    glass_finish = model.material("glass_finish", rgba=(0.10, 0.18, 0.22, 0.55))
    accent_finish = model.material("accent_finish", rgba=(0.52, 0.53, 0.56, 1.0))

    body = model.part("body")
    body.visual(_body_shell_mesh(), material=body_finish, name="housing_shell")
    body.visual(
        Cylinder(radius=LENS_BARREL_RADIUS, length=LENS_BARREL_LENGTH),
        origin=Origin(
            xyz=(BODY_LEN * 0.5 + LENS_BARREL_LENGTH * 0.5 - 0.0005, 0.0, 0.0),
            rpy=(0.0, math.pi * 0.5, 0.0),
        ),
        material=lens_finish,
        name="lens_barrel",
    )
    body.visual(
        Cylinder(radius=0.0285, length=0.002),
        origin=Origin(
            xyz=(0.069, 0.0, 0.0),
            rpy=(0.0, math.pi * 0.5, 0.0),
        ),
        material=ring_finish,
        name="lens_shoulder",
    )
    body.visual(
        Cylinder(radius=0.0205, length=0.002),
        origin=Origin(
            xyz=(BODY_LEN * 0.5 + LENS_BARREL_LENGTH - 0.001, 0.0, 0.0),
            rpy=(0.0, math.pi * 0.5, 0.0),
        ),
        material=glass_finish,
        name="lens_glass",
    )
    body.visual(
        Box((0.090, 0.004, 0.046)),
        origin=Origin(xyz=(0.006, -0.044, -0.002)),
        material=grip_finish,
        name="handgrip_pad",
    )
    body.visual(
        Box((0.014, 0.004, MONITOR_HEIGHT - 0.004)),
        origin=Origin(xyz=(MONITOR_HINGE_X, 0.031, MONITOR_HINGE_Z + MONITOR_HEIGHT * 0.5)),
        material=accent_finish,
        name="monitor_mount",
    )
    body.visual(
        Box((PORT_COVER_LEN + 0.004, 0.0025, 0.008)),
        origin=Origin(xyz=(PORT_COVER_HINGE_X, 0.03025, PORT_COVER_HINGE_Z)),
        material=accent_finish,
        name="port_mount",
    )

    lens_ring = model.part("lens_ring")
    lens_ring.visual(_lens_ring_mesh(), material=ring_finish, name="ring_shell")

    side_monitor = model.part("side_monitor")
    side_monitor.visual(
        Box((MONITOR_LEN, MONITOR_THICKNESS, MONITOR_HEIGHT)),
        origin=Origin(
            xyz=(0.0035 + MONITOR_LEN * 0.5, MONITOR_THICKNESS * 0.5, MONITOR_HEIGHT * 0.5)
        ),
        material=trim_finish,
        name="screen_panel",
    )
    side_monitor.visual(
        Box((MONITOR_LEN - 0.018, 0.0014, MONITOR_HEIGHT - 0.016)),
        origin=Origin(
            xyz=(0.0035 + MONITOR_LEN * 0.5, 0.0007, MONITOR_HEIGHT * 0.5),
        ),
        material=glass_finish,
        name="screen_glass",
    )
    side_monitor.visual(
        Cylinder(radius=MONITOR_HINGE_RADIUS, length=MONITOR_HEIGHT - 0.004),
        origin=Origin(xyz=(0.0, MONITOR_HINGE_RADIUS, MONITOR_HEIGHT * 0.5)),
        material=trim_finish,
        name="monitor_hinge",
    )

    port_cover = model.part("port_cover")
    port_cover.visual(
        Box((PORT_COVER_LEN, PORT_COVER_THICKNESS, PORT_COVER_HEIGHT)),
        origin=Origin(xyz=(0.0, PORT_COVER_THICKNESS * 0.5, PORT_COVER_HEIGHT * 0.5)),
        material=trim_finish,
        name="cover_panel",
    )
    port_cover.visual(
        Cylinder(radius=PORT_COVER_HINGE_RADIUS, length=PORT_COVER_LEN),
        origin=Origin(
            xyz=(0.0, PORT_COVER_HINGE_RADIUS, 0.0),
            rpy=(0.0, math.pi * 0.5, 0.0),
        ),
        material=body_finish,
        name="cover_hinge",
    )

    model.articulation(
        "body_to_lens_ring",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=lens_ring,
        origin=Origin(xyz=(BODY_LEN * 0.5 + LENS_BARREL_LENGTH - 0.004, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.4, velocity=8.0),
    )
    model.articulation(
        "body_to_side_monitor",
        ArticulationType.REVOLUTE,
        parent=body,
        child=side_monitor,
        origin=Origin(xyz=(MONITOR_HINGE_X, MONITOR_HINGE_Y, MONITOR_HINGE_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=1.0,
            velocity=2.5,
            lower=0.0,
            upper=1.95,
        ),
    )
    model.articulation(
        "body_to_port_cover",
        ArticulationType.REVOLUTE,
        parent=body,
        child=port_cover,
        origin=Origin(xyz=(PORT_COVER_HINGE_X, PORT_COVER_HINGE_Y, PORT_COVER_HINGE_Z)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.4,
            velocity=3.0,
            lower=0.0,
            upper=1.35,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
