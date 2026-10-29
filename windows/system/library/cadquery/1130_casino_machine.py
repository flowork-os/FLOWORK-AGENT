# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, casino_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: casino_machine

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
SHELF_TOP_Z = 0.276
BUTTON_TRAVEL = 0.006
TRAY_HINGE_XYZ = (0.0, -0.207, 0.085)
TRAY_OPEN_ANGLE = 1.05
def _base_with_recess() -> cq.Workplane:
    """Lower cabinet block with a blind, real cash tray pocket cut into it."""
    width = 0.56
    depth = 0.38
    height = 0.235
    front_y = -depth / 2.0

    body = cq.Workplane("XY").box(width, depth, height).translate((0.0, 0.0, height / 2.0))

    # A blind rectangular subtraction from the front creates the actual tray
    # sidewalls, top, bottom, and back instead of a painted-on rectangle.
    pocket = (
        cq.Workplane("XY")
        .box(0.34, 0.110, 0.092)
        .translate((0.0, front_y + 0.110 / 2.0 - 0.014, 0.126))
    )
    return body.cut(pocket)
def _button_ring() -> cq.Workplane:
    return cq.Workplane("XY").circle(0.033).circle(0.0255).extrude(0.006)
def _rx(local: tuple[float, float, float], angle: float) -> tuple[float, float, float]:
    x, y, z = local
    ca = math.cos(angle)
    sa = math.sin(angle)
    return (x, y * ca - z * sa, y * sa + z * ca)
def _panel_point(
    center: tuple[float, float, float],
    angle: float,
    local: tuple[float, float, float],
) -> tuple[float, float, float]:
    dx, dy, dz = _rx(local, angle)
    return (center[0] + dx, center[1] + dy, center[2] + dz)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bar_top_video_poker")

    shell = model.material("warm_black_plastic", rgba=(0.015, 0.014, 0.013, 1.0))
    side = model.material("dark_burgundy_side", rgba=(0.18, 0.020, 0.035, 1.0))
    shelf_mat = model.material("satin_control_shelf", rgba=(0.055, 0.052, 0.050, 1.0))
    glass = model.material("blue_black_glass", rgba=(0.015, 0.040, 0.070, 1.0))
    screen_blue = model.material("screen_blue", rgba=(0.05, 0.30, 0.90, 1.0))
    screen_green = model.material("screen_green", rgba=(0.05, 0.80, 0.28, 1.0))
    screen_gold = model.material("screen_gold", rgba=(1.00, 0.68, 0.08, 1.0))
    tray_mat = model.material("deep_tray_black", rgba=(0.005, 0.005, 0.006, 1.0))
    hinge_mat = model.material("brushed_hinge_pin", rgba=(0.58, 0.55, 0.50, 1.0))
    red = model.material("red_play_button", rgba=(0.86, 0.04, 0.025, 1.0))
    amber = model.material("amber_play_button", rgba=(1.0, 0.48, 0.03, 1.0))
    green = model.material("green_play_button", rgba=(0.05, 0.72, 0.16, 1.0))
    blue = model.material("blue_play_button", rgba=(0.05, 0.18, 0.85, 1.0))

    cabinet = model.part("cabinet")
    cabinet.visual(
        mesh_from_cadquery(_base_with_recess(), "cabinet_base", tolerance=0.001),
        material=shell,
        name="cabinet_base",
    )

    # Short horizontal button shelf protruding from the shallow countertop body.
    cabinet.visual(
        Box((0.54, 0.205, 0.044)),
        origin=Origin(xyz=(0.0, -0.125, 0.254)),
        material=shelf_mat,
        name="control_shelf",
    )
    cabinet.visual(
        Box((0.54, 0.018, 0.030)),
        origin=Origin(xyz=(0.0, -0.236, 0.290)),
        material=shell,
        name="front_shelf_lip",
    )

    # Leaning upper display pod: a shallow slab attached to the shelf and base.
    panel_angle = -0.365
    panel_center = (0.0, 0.006, 0.420)
    cabinet.visual(
        Box((0.55, 0.055, 0.290)),
        origin=Origin(xyz=panel_center, rpy=(panel_angle, 0.0, 0.0)),
        material=side,
        name="sloped_screen_pod",
    )

    # One dark screen with a raised frame and a few thin "lit" UI strips.
    cabinet.visual(
        Box((0.405, 0.006, 0.180)),
        origin=Origin(
            xyz=_panel_point(panel_center, panel_angle, (0.0, -0.0295, 0.020)),
            rpy=(panel_angle, 0.0, 0.0),
        ),
        material=glass,
        name="screen_glass",
    )
    for name, local, size in (
        ("screen_bezel_top", (0.0, -0.031, 0.132), (0.455, 0.014, 0.030)),
        ("screen_bezel_bottom", (0.0, -0.031, -0.094), (0.455, 0.014, 0.030)),
        ("screen_bezel_side_0", (-0.230, -0.031, 0.020), (0.030, 0.014, 0.224)),
        ("screen_bezel_side_1", (0.230, -0.031, 0.020), (0.030, 0.014, 0.224)),
    ):
        cabinet.visual(
            Box(size),
            origin=Origin(xyz=_panel_point(panel_center, panel_angle, local), rpy=(panel_angle, 0.0, 0.0)),
            material=shell,
            name=name,
        )
    for name, local, size, mat in (
        ("screen_title_bar", (0.0, -0.0335, 0.080), (0.310, 0.004, 0.018), screen_blue),
        ("screen_card_row", (-0.070, -0.0335, 0.020), (0.185, 0.004, 0.040), screen_gold),
        ("screen_credit_bar", (0.065, -0.0335, -0.052), (0.255, 0.004, 0.016), screen_green),
    ):
        cabinet.visual(
            Box(size),
            origin=Origin(xyz=_panel_point(panel_center, panel_angle, local), rpy=(panel_angle, 0.0, 0.0)),
            material=mat,
            name=name,
        )

    # Recess interior treatment: floor and back wall are set well behind the
    # front face, so the cash-out area reads as a true pocket.
    cabinet.visual(
        Box((0.310, 0.076, 0.006)),
        origin=Origin(xyz=(0.0, -0.143, 0.083)),
        material=tray_mat,
        name="tray_floor",
    )
    cabinet.visual(
        Box((0.310, 0.006, 0.070)),
        origin=Origin(xyz=(0.0, -0.097, 0.126)),
        material=tray_mat,
        name="tray_back",
    )
    cabinet.visual(
        Box((0.024, 0.024, 0.030)),
        origin=Origin(xyz=(-0.184, -0.197, 0.084)),
        material=shell,
        name="hinge_bracket_0",
    )
    cabinet.visual(
        Box((0.024, 0.024, 0.030)),
        origin=Origin(xyz=(0.184, -0.197, 0.084)),
        material=shell,
        name="hinge_bracket_1",
    )

    ring_mesh = mesh_from_cadquery(_button_ring(), "button_ring", tolerance=0.0008)
    button_xs = (-0.180, -0.090, 0.0, 0.090, 0.180)
    button_mats = (red, amber, green, blue, red)
    for i, x in enumerate(button_xs):
        cabinet.visual(
            ring_mesh,
            origin=Origin(xyz=(x, -0.158, SHELF_TOP_Z)),
            material=tray_mat,
            name=f"button_ring_{i}",
        )

    tray_flap = model.part("tray_flap")
    tray_flap.visual(
        Box((0.300, 0.010, 0.068)),
        origin=Origin(xyz=(0.0, 0.011, 0.034)),
        material=shelf_mat,
        name="flap_panel",
    )
    tray_flap.visual(
        Cylinder(radius=0.007, length=0.344),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=hinge_mat,
        name="flap_hinge_barrel",
    )
    tray_flap.visual(
        Box((0.120, 0.010, 0.012)),
        origin=Origin(xyz=(0.0, 0.010, 0.056)),
        material=tray_mat,
        name="flap_pull_lip",
    )
    model.articulation(
        "cabinet_to_tray_flap",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=tray_flap,
        origin=Origin(xyz=TRAY_HINGE_XYZ),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=1.2, lower=0.0, upper=TRAY_OPEN_ANGLE),
    )

    for i, (x, mat) in enumerate(zip(button_xs, button_mats)):
        button = model.part(f"button_{i}")
        button.visual(
            Cylinder(radius=0.023, length=0.014),
            origin=Origin(xyz=(0.0, 0.0, 0.007)),
            material=mat,
            name="button_cap",
        )
        button.visual(
            Cylinder(radius=0.016, length=0.006),
            origin=Origin(xyz=(0.0, 0.0, -0.003)),
            material=tray_mat,
            name="button_stem",
        )
        model.articulation(
            f"cabinet_to_button_{i}",
            ArticulationType.PRISMATIC,
            parent=cabinet,
            child=button,
            origin=Origin(xyz=(x, -0.158, SHELF_TOP_Z + 0.006)),
            axis=(0.0, 0.0, 1.0),
            motion_limits=MotionLimits(effort=4.0, velocity=0.08, lower=-BUTTON_TRAVEL, upper=0.0),
        )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
