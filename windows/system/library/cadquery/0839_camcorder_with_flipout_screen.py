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
BODY_LEN = 0.108
BODY_DEPTH = 0.046
BODY_HEIGHT = 0.066
LENS_Z = 0.004
GRIP_LEN = 0.088
GRIP_DEPTH = 0.020
GRIP_HEIGHT = 0.052
GRIP_CENTER = (0.004, -0.028, -0.003)
BATTERY_LEN = 0.028
BATTERY_DEPTH = 0.036
BATTERY_HEIGHT = 0.056
BATTERY_CENTER = (-0.058, 0.0, 0.002)
TOP_RIDGE_LEN = 0.056
TOP_RIDGE_DEPTH = 0.028
TOP_RIDGE_HEIGHT = 0.014
TOP_RIDGE_CENTER = (-0.008, 0.0, 0.034)
SCREEN_WIDTH = 0.070
SCREEN_THICKNESS = 0.008
SCREEN_HEIGHT = 0.046
SCREEN_HINGE_X = -0.034
SCREEN_HINGE_Y = BODY_DEPTH * 0.5
SCREEN_HINGE_Z = 0.004
RING_OUTER_RADIUS = 0.0245
RING_INNER_RADIUS = 0.0186
RING_LENGTH = 0.012
RING_CENTER_X = 0.068
HATCH_WIDTH = 0.026
HATCH_THICKNESS = 0.003
HATCH_HEIGHT = 0.020
HATCH_HINGE_X = 0.016
HATCH_HINGE_Y = GRIP_CENTER[1] - (GRIP_DEPTH * 0.5)
HATCH_HINGE_Z = -0.022
def _rounded_box(size: tuple[float, float, float], radius: float, center: tuple[float, float, float]):
    solid = cq.Workplane("XY").box(*size)
    if radius > 0.0:
        solid = solid.edges("|Z").fillet(radius)
    return solid.translate(center)
def _rounded_xz_panel(
    width: float,
    thickness: float,
    height: float,
    radius: float,
    center: tuple[float, float, float],
):
    solid = cq.Workplane("XY").box(width, thickness, height)
    if radius > 0.0:
        solid = solid.edges("|Y").fillet(radius)
    return solid.translate(center)
def _z_cylinder(radius: float, length: float, center: tuple[float, float, float]):
    x, y, z = center
    return cq.Workplane("XY").circle(radius).extrude(length).translate((x, y, z - length * 0.5))
def _x_annulus(outer_radius: float, inner_radius: float, length: float, center_x: float = 0.0):
    return (
        cq.Workplane("YZ")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length)
        .translate((center_x - length * 0.5, 0.0, 0.0))
    )
def _body_shell_mesh():
    shell = _rounded_box((BODY_LEN, BODY_DEPTH, BODY_HEIGHT), 0.010, (0.0, 0.0, 0.0))
    grip = _rounded_box((GRIP_LEN, GRIP_DEPTH, GRIP_HEIGHT), 0.007, GRIP_CENTER)
    battery = _rounded_box((BATTERY_LEN, BATTERY_DEPTH, BATTERY_HEIGHT), 0.006, BATTERY_CENTER)
    ridge = _rounded_box((TOP_RIDGE_LEN, TOP_RIDGE_DEPTH, TOP_RIDGE_HEIGHT), 0.004, TOP_RIDGE_CENTER)
    shell = shell.union(grip).union(battery).union(ridge)
    return mesh_from_cadquery(shell, "camcorder_body_shell")
def _screen_frame_mesh():
    frame = _rounded_xz_panel(
        SCREEN_WIDTH,
        SCREEN_THICKNESS,
        SCREEN_HEIGHT,
        0.0045,
        (SCREEN_WIDTH * 0.5, SCREEN_THICKNESS * 0.5, 0.0),
    )
    pocket = cq.Workplane("XY").box(
        SCREEN_WIDTH * 0.78,
        SCREEN_THICKNESS * 0.26,
        SCREEN_HEIGHT * 0.72,
    ).translate((SCREEN_WIDTH * 0.54, SCREEN_THICKNESS * 0.13, 0.0))
    hinge_spine = _z_cylinder(0.0028, SCREEN_HEIGHT * 0.92, (0.0018, 0.0030, 0.0))
    frame = frame.cut(pocket).union(hinge_spine)
    return mesh_from_cadquery(frame, "camcorder_screen_frame")
def _focus_ring_mesh():
    ring = _x_annulus(RING_OUTER_RADIUS, RING_INNER_RADIUS, RING_LENGTH)
    rib = _x_annulus(RING_OUTER_RADIUS + 0.0008, RING_INNER_RADIUS, 0.0012)
    ring = ring.union(rib.translate((-0.0032, 0.0, 0.0)))
    ring = ring.union(rib)
    ring = ring.union(rib.translate((0.0032, 0.0, 0.0)))
    return mesh_from_cadquery(ring, "camcorder_focus_ring")
def _hatch_mesh():
    panel = _rounded_xz_panel(
        HATCH_WIDTH,
        HATCH_THICKNESS,
        HATCH_HEIGHT,
        0.0024,
        (0.0, -HATCH_THICKNESS * 0.5, HATCH_HEIGHT * 0.5),
    )
    hinge = (
        cq.Workplane("YZ")
        .circle(0.0015)
        .extrude(HATCH_WIDTH * 0.92)
        .translate((-HATCH_WIDTH * 0.46, -HATCH_THICKNESS * 0.5, 0.0015))
    )
    return mesh_from_cadquery(panel.union(hinge), "camcorder_card_hatch")
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="travel_camcorder")

    body_black = model.material("body_black", rgba=(0.10, 0.11, 0.12, 1.0))
    trim_gray = model.material("trim_gray", rgba=(0.23, 0.24, 0.26, 1.0))
    ring_rubber = model.material("ring_rubber", rgba=(0.07, 0.07, 0.08, 1.0))
    glass = model.material("glass", rgba=(0.20, 0.30, 0.36, 0.42))
    display_glass = model.material("display_glass", rgba=(0.16, 0.26, 0.31, 0.55))

    body = model.part("body")
    body.visual(_body_shell_mesh(), material=body_black, name="shell")
    body.visual(
        Cylinder(radius=0.017, length=0.039),
        origin=Origin(xyz=(0.0685, 0.0, LENS_Z), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=trim_gray,
        name="lens_core",
    )
    body.visual(
        Cylinder(radius=0.023, length=0.014),
        origin=Origin(xyz=(0.055, 0.0, LENS_Z), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=body_black,
        name="rear_shroud",
    )
    body.visual(
        Cylinder(radius=0.0215, length=0.012),
        origin=Origin(xyz=(0.082, 0.0, LENS_Z), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=body_black,
        name="front_hood",
    )
    body.visual(
        Cylinder(radius=0.0155, length=0.0012),
        origin=Origin(xyz=(0.0886, 0.0, LENS_Z), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=glass,
        name="lens_glass",
    )
    body.visual(
        Box((0.020, 0.004, 0.012)),
        origin=Origin(xyz=(0.012, -0.039, 0.000)),
        material=trim_gray,
        name="grip_strap_pad",
    )

    screen = model.part("screen")
    screen.visual(_screen_frame_mesh(), material=body_black, name="screen_frame")
    screen.visual(
        Box((SCREEN_WIDTH * 0.70, 0.0012, SCREEN_HEIGHT * 0.62)),
        origin=Origin(xyz=(SCREEN_WIDTH * 0.56, 0.00148, 0.0)),
        material=display_glass,
        name="display",
    )

    focus_ring = model.part("focus_ring")
    focus_ring.visual(_focus_ring_mesh(), material=ring_rubber, name="ring_shell")

    card_hatch = model.part("card_hatch")
    card_hatch.visual(_hatch_mesh(), material=trim_gray, name="hatch_panel")

    model.articulation(
        "screen_hinge",
        ArticulationType.REVOLUTE,
        parent=body,
        child=screen,
        origin=Origin(xyz=(SCREEN_HINGE_X, SCREEN_HINGE_Y, SCREEN_HINGE_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=0.5,
            velocity=2.5,
            lower=0.0,
            upper=2.1,
        ),
    )
    model.articulation(
        "focus_spin",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=focus_ring,
        origin=Origin(xyz=(RING_CENTER_X, 0.0, LENS_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.08,
            velocity=12.0,
        ),
    )
    model.articulation(
        "card_hatch_hinge",
        ArticulationType.REVOLUTE,
        parent=body,
        child=card_hatch,
        origin=Origin(xyz=(HATCH_HINGE_X, HATCH_HINGE_Y, HATCH_HINGE_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.15,
            velocity=2.0,
            lower=0.0,
            upper=1.45,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
