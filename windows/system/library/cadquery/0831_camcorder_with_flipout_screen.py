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
def _lens_barrel_shape() -> cq.Workplane:
    collar = cq.Workplane("XY").box(0.018, 0.058, 0.058).translate((0.009, 0.0, 0.0))
    barrel = (
        cq.Workplane("YZ")
        .circle(0.0262)
        .extrude(0.104)
        .cut(cq.Workplane("YZ").circle(0.0218).extrude(0.104))
    )
    hood = (
        cq.Workplane("YZ")
        .circle(0.0305)
        .circle(0.0240)
        .extrude(0.018)
        .translate((0.104, 0.0, 0.0))
    )
    front_bezel = (
        cq.Workplane("YZ")
        .circle(0.033)
        .circle(0.0255)
        .extrude(0.006)
        .translate((0.122, 0.0, 0.0))
    )
    return collar.union(barrel).union(hood).union(front_bezel)
def _focus_ring_shape() -> cq.Workplane:
    ring = (
        cq.Workplane("YZ")
        .circle(0.0298)
        .extrude(0.018)
        .translate((-0.009, 0.0, 0.0))
        .cut(
            cq.Workplane("YZ")
            .circle(0.0260)
            .extrude(0.022)
            .translate((-0.011, 0.0, 0.0))
        )
    )
    for angle_deg in range(0, 360, 24):
        grip = (
            cq.Workplane("XY")
            .box(0.018, 0.0028, 0.0055)
            .translate((0.0, 0.0292, 0.0))
            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg)
        )
        ring = ring.union(grip)
    return ring
def _main_shell_shape() -> cq.Workplane:
    return (
        cq.Workplane("YZ")
        .rect(0.078, 0.082)
        .workplane(offset=0.050)
        .rect(0.076, 0.082)
        .workplane(offset=0.040)
        .rect(0.070, 0.078)
        .workplane(offset=0.030)
        .rect(0.060, 0.070)
        .loft(combine=True)
    )
def _grip_shape() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .rect(0.066, 0.022)
        .workplane(offset=0.038)
        .center(0.003, 0.0)
        .rect(0.060, 0.020)
        .workplane(offset=0.048)
        .center(0.010, 0.0)
        .rect(0.042, 0.018)
        .loft(combine=True)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="prosumer_camcorder")

    body_black = model.material("body_black", rgba=(0.12, 0.12, 0.13, 1.0))
    shell_black = model.material("shell_black", rgba=(0.17, 0.17, 0.18, 1.0))
    rubber_black = model.material("rubber_black", rgba=(0.07, 0.07, 0.07, 1.0))
    dark_grey = model.material("dark_grey", rgba=(0.23, 0.23, 0.24, 1.0))
    metal = model.material("metal", rgba=(0.54, 0.56, 0.58, 1.0))
    glass = model.material("glass", rgba=(0.20, 0.34, 0.40, 0.45))
    screen_black = model.material("screen_black", rgba=(0.06, 0.06, 0.07, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_main_shell_shape(), "camcorder_main_shell"),
        origin=Origin(xyz=(-0.065, 0.0, 0.041)),
        material=body_black,
        name="main_shell",
    )
    body.visual(
        Box((0.074, 0.076, 0.022)),
        origin=Origin(xyz=(0.012, 0.0, 0.086)),
        material=shell_black,
        name="upper_shell",
    )
    body.visual(
        Box((0.040, 0.058, 0.068)),
        origin=Origin(xyz=(-0.078, 0.0, 0.049)),
        material=shell_black,
        name="battery_pack",
    )
    body.visual(
        Box((0.022, 0.060, 0.060)),
        origin=Origin(xyz=(0.060, 0.0, 0.044)),
        material=body_black,
        name="front_cheek",
    )
    body.visual(
        Box((0.016, 0.016, 0.030)),
        origin=Origin(xyz=(0.050, 0.0, 0.093)),
        material=body_black,
        name="handle_front_post",
    )
    body.visual(
        Box((0.016, 0.016, 0.030)),
        origin=Origin(xyz=(-0.010, 0.0, 0.093)),
        material=body_black,
        name="handle_rear_post",
    )
    body.visual(
        Box((0.084, 0.016, 0.012)),
        origin=Origin(xyz=(0.020, 0.0, 0.114)),
        material=body_black,
        name="handle_bridge",
    )
    body.visual(
        mesh_from_cadquery(_grip_shape(), "camcorder_grip_shell"),
        origin=Origin(xyz=(0.000, -0.048, 0.002)),
        material=rubber_black,
        name="grip_shell",
    )
    body.visual(
        Box((0.052, 0.004, 0.056)),
        origin=Origin(xyz=(0.034, -0.059, 0.047)),
        material=dark_grey,
        name="hand_strap",
    )
    body.visual(
        Cylinder(radius=0.010, length=0.024),
        origin=Origin(xyz=(-0.096, 0.0, 0.068), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=screen_black,
        name="eyepiece_tube",
    )
    body.visual(
        Box((0.012, 0.026, 0.018)),
        origin=Origin(xyz=(-0.108, 0.0, 0.068)),
        material=rubber_black,
        name="eyecup",
    )
    body.visual(
        Box((0.008, 0.006, 0.014)),
        origin=Origin(xyz=(-0.055, 0.034, 0.062)),
        material=body_black,
        name="monitor_hinge_upper",
    )
    body.visual(
        Box((0.008, 0.006, 0.014)),
        origin=Origin(xyz=(-0.055, 0.034, 0.026)),
        material=body_black,
        name="monitor_hinge_lower",
    )
    body.visual(
        Box((0.010, 0.008, 0.054)),
        origin=Origin(xyz=(-0.055, 0.031, 0.044)),
        material=body_black,
        name="monitor_hinge_plate",
    )
    body.visual(
        Box((0.020, 0.016, 0.016)),
        origin=Origin(xyz=(-0.045, -0.016, 0.090)),
        material=dark_grey,
        name="dial_plinth",
    )

    lens_barrel = model.part("lens_barrel")
    lens_barrel.visual(
        mesh_from_cadquery(_lens_barrel_shape(), "camcorder_lens_barrel"),
        material=shell_black,
        name="barrel_shell",
    )

    focus_ring = model.part("focus_ring")
    focus_ring.visual(
        mesh_from_cadquery(_focus_ring_shape(), "camcorder_focus_ring"),
        material=rubber_black,
        name="focus_ring",
    )

    monitor = model.part("monitor")
    monitor.visual(
        Cylinder(radius=0.0032, length=0.022),
        origin=Origin(xyz=(0.0, 0.0010, 0.044)),
        material=metal,
        name="monitor_hinge",
    )
    monitor.visual(
        Box((0.010, 0.006, 0.050)),
        origin=Origin(xyz=(0.005, 0.0030, 0.044)),
        material=screen_black,
        name="monitor_arm",
    )
    monitor.visual(
        Box((0.074, 0.007, 0.050)),
        origin=Origin(xyz=(0.037, 0.0035, 0.044)),
        material=screen_black,
        name="monitor_panel",
    )
    monitor.visual(
        Box((0.058, 0.0016, 0.040)),
        origin=Origin(xyz=(0.039, 0.0011, 0.044)),
        material=glass,
        name="screen_glass",
    )
    monitor.visual(
        Box((0.070, 0.0015, 0.046)),
        origin=Origin(xyz=(0.037, 0.0063, 0.044)),
        material=dark_grey,
        name="monitor_back",
    )

    mode_dial = model.part("mode_dial")
    mode_dial.visual(
        Cylinder(radius=0.004, length=0.004),
        origin=Origin(xyz=(0.0, 0.0, 0.002)),
        material=metal,
        name="dial_spindle",
    )
    mode_dial.visual(
        Cylinder(radius=0.017, length=0.006),
        origin=Origin(xyz=(0.0, 0.0, 0.005)),
        material=dark_grey,
        name="dial_body",
    )
    mode_dial.visual(
        Cylinder(radius=0.015, length=0.003),
        origin=Origin(xyz=(0.0, 0.0, 0.0095)),
        material=body_black,
        name="dial_cap",
    )
    mode_dial.visual(
        Box((0.010, 0.0025, 0.0015)),
        origin=Origin(xyz=(0.006, 0.0, 0.0108)),
        material=metal,
        name="dial_pointer",
    )

    model.articulation(
        "body_to_lens_barrel",
        ArticulationType.FIXED,
        parent=body,
        child=lens_barrel,
        origin=Origin(xyz=(0.071, 0.0, 0.044)),
    )
    model.articulation(
        "lens_barrel_to_focus_ring",
        ArticulationType.CONTINUOUS,
        parent=lens_barrel,
        child=focus_ring,
        origin=Origin(xyz=(0.034, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.25, velocity=12.0),
    )
    model.articulation(
        "body_to_monitor",
        ArticulationType.REVOLUTE,
        parent=body,
        child=monitor,
        origin=Origin(xyz=(-0.055, 0.0405, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=1.0,
            velocity=2.5,
            lower=0.0,
            upper=math.radians(105.0),
        ),
    )
    model.articulation(
        "body_to_mode_dial",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=mode_dial,
        origin=Origin(xyz=(-0.045, -0.016, 0.0975)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.15, velocity=8.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
