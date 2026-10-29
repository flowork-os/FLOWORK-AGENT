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
BODY_L = 0.125
BODY_W = 0.057
BODY_H = 0.066
SCREEN_W = 0.074
SCREEN_H = 0.050
SCREEN_T = 0.007
SCREEN_Z = 0.010
HINGE_X = -0.034
BUTTON_XS = (-0.015, 0.001, 0.017)
BUTTON_Z = -0.021
BUTTON_SIZE = (0.010, 0.0024, 0.0052)
BUTTON_TRAVEL = 0.0012
LENS_Z = 0.004
FOCUS_RING_X = BODY_L * 0.5 + 0.032
def _make_body_shape() -> cq.Workplane:
    body = cq.Workplane("XY").box(BODY_L, BODY_W, BODY_H)
    body = body.edges("|Z").fillet(0.007)

    top_spine = (
        cq.Workplane("XY")
        .box(0.060, BODY_W * 0.84, 0.010)
        .translate((-0.008, 0.0, BODY_H * 0.5 + 0.005))
    )
    body = body.union(top_spine)

    screen_pocket = (
        cq.Workplane("XY")
        .box(SCREEN_W + 0.004, 0.0026, SCREEN_H + 0.004)
        .translate((0.001, BODY_W * 0.5 - 0.0013, SCREEN_Z))
    )
    hinge_notch = (
        cq.Workplane("XY")
        .box(0.009, 0.0042, SCREEN_H + 0.006)
        .translate((HINGE_X, BODY_W * 0.5 - 0.0021, SCREEN_Z))
    )
    body = body.cut(screen_pocket).cut(hinge_notch)

    for button_x in BUTTON_XS:
        body = body.cut(
            cq.Workplane("XY")
            .box(BUTTON_SIZE[0] + 0.0012, BUTTON_TRAVEL + 0.0002, BUTTON_SIZE[2] + 0.0012)
            .translate((button_x, BODY_W * 0.5 - (BUTTON_TRAVEL + 0.0002) * 0.5, BUTTON_Z))
        )
        body = body.cut(
            cq.Workplane("XY")
            .box(0.0060, 0.0060, 0.0038)
            .translate((button_x, BODY_W * 0.5 - 0.0030, BUTTON_Z))
        )

    return body
def _make_focus_ring_shape() -> cq.Workplane:
    base = (
        cq.Workplane("YZ")
        .circle(0.022)
        .circle(0.0128)
        .extrude(0.014)
        .translate((-0.007, 0.0, 0.0))
    )
    rear_rib = (
        cq.Workplane("YZ")
        .circle(0.0228)
        .circle(0.0128)
        .extrude(0.0016)
        .translate((-0.0053, 0.0, 0.0))
    )
    front_rib = (
        cq.Workplane("YZ")
        .circle(0.0228)
        .circle(0.0128)
        .extrude(0.0016)
        .translate((0.0037, 0.0, 0.0))
    )
    return base.union(rear_rib).union(front_rib)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="travel_camcorder")

    body_shell = model.material("body_shell", rgba=(0.20, 0.21, 0.23, 1.0))
    trim_dark = model.material("trim_dark", rgba=(0.08, 0.09, 0.10, 1.0))
    rubber_dark = model.material("rubber_dark", rgba=(0.13, 0.14, 0.15, 1.0))
    glass_dark = model.material("glass_dark", rgba=(0.18, 0.28, 0.34, 0.55))
    button_grey = model.material("button_grey", rgba=(0.60, 0.62, 0.65, 1.0))
    strap_black = model.material("strap_black", rgba=(0.10, 0.10, 0.11, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_make_body_shape(), "camcorder_body"),
        material=body_shell,
        name="body_shell",
    )
    body.visual(
        Box((SCREEN_W - 0.006, 0.0010, SCREEN_H - 0.008)),
        origin=Origin(xyz=(0.001, BODY_W * 0.5 - 0.0021, SCREEN_Z)),
        material=trim_dark,
        name="screen_bay",
    )
    body.visual(
        Box((0.014, 0.022, 0.014)),
        origin=Origin(xyz=(-BODY_L * 0.5 - 0.007, 0.0, 0.016)),
        material=trim_dark,
        name="eyepiece",
    )
    body.visual(
        Box((0.068, 0.004, 0.028)),
        origin=Origin(xyz=(0.008, -BODY_W * 0.5 - 0.002, -0.002)),
        material=strap_black,
        name="hand_strap",
    )
    body.visual(
        Cylinder(radius=0.024, length=0.006),
        origin=Origin(
            xyz=(BODY_L * 0.5 + 0.003, 0.0, LENS_Z),
            rpy=(0.0, math.pi * 0.5, 0.0),
        ),
        material=trim_dark,
        name="lens_mount",
    )
    body.visual(
        Cylinder(radius=0.020, length=0.018),
        origin=Origin(
            xyz=(BODY_L * 0.5 + 0.016, 0.0, LENS_Z),
            rpy=(0.0, math.pi * 0.5, 0.0),
        ),
        material=trim_dark,
        name="lens_barrel",
    )
    body.visual(
        Cylinder(radius=0.011, length=0.058),
        origin=Origin(
            xyz=(BODY_L * 0.5 + 0.029, 0.0, LENS_Z),
            rpy=(0.0, math.pi * 0.5, 0.0),
        ),
        material=trim_dark,
        name="lens_core",
    )
    body.visual(
        Cylinder(radius=0.0185, length=0.018),
        origin=Origin(
            xyz=(BODY_L * 0.5 + 0.048, 0.0, LENS_Z),
            rpy=(0.0, math.pi * 0.5, 0.0),
        ),
        material=trim_dark,
        name="front_bezel",
    )
    body.visual(
        Cylinder(radius=0.015, length=0.002),
        origin=Origin(
            xyz=(BODY_L * 0.5 + 0.058, 0.0, LENS_Z),
            rpy=(0.0, math.pi * 0.5, 0.0),
        ),
        material=glass_dark,
        name="lens_glass",
    )

    focus_ring = model.part("focus_ring")
    focus_ring.visual(
        mesh_from_cadquery(_make_focus_ring_shape(), "focus_ring"),
        material=rubber_dark,
        name="focus_ring",
    )
    focus_ring.visual(
        Box((0.004, 0.0014, 0.0012)),
        origin=Origin(xyz=(0.0, 0.0, 0.0222)),
        material=button_grey,
        name="focus_index_mark",
    )

    model.articulation(
        "body_to_focus_ring",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=focus_ring,
        origin=Origin(xyz=(FOCUS_RING_X, 0.0, LENS_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.2, velocity=12.0),
    )

    flip_screen = model.part("flip_screen")
    flip_screen.visual(
        Cylinder(radius=0.0034, length=SCREEN_H),
        origin=Origin(),
        material=trim_dark,
        name="screen_spine",
    )
    flip_screen.visual(
        Box((SCREEN_W, SCREEN_T, SCREEN_H)),
        origin=Origin(xyz=(SCREEN_W * 0.5, SCREEN_T * 0.5, 0.0)),
        material=body_shell,
        name="screen_housing",
    )
    flip_screen.visual(
        Box((SCREEN_W - 0.012, 0.0014, SCREEN_H - 0.010)),
        origin=Origin(xyz=(SCREEN_W * 0.5, 0.0011, 0.0)),
        material=glass_dark,
        name="display",
    )

    model.articulation(
        "body_to_flip_screen",
        ArticulationType.REVOLUTE,
        parent=body,
        child=flip_screen,
        origin=Origin(xyz=(HINGE_X, BODY_W * 0.5 + 0.0005, SCREEN_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=1.2,
            velocity=2.0,
            lower=0.0,
            upper=2.35,
        ),
    )

    for index, button_x in enumerate(BUTTON_XS):
        button = model.part(f"button_{index}")
        button.visual(
            Box(BUTTON_SIZE),
            material=button_grey,
            name="button_cap",
        )
        button.visual(
            Box((0.0060, 0.0048, 0.0038)),
            origin=Origin(xyz=(0.0, -0.0036, 0.0)),
            material=button_grey,
            name="button_stem",
        )
        model.articulation(
            f"body_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(
                xyz=(
                    button_x,
                    BODY_W * 0.5 + BUTTON_SIZE[1] * 0.5,
                    BUTTON_Z,
                )
            ),
            axis=(0.0, -1.0, 0.0),
            motion_limits=MotionLimits(
                effort=4.0,
                velocity=0.04,
                lower=0.0,
                upper=BUTTON_TRAVEL,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
