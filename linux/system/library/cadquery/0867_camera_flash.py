# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_flash, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_flash

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
BLACK = Material("satin_black_plastic", rgba=(0.01, 0.01, 0.012, 1.0))
RUBBER = Material("matte_rubber", rgba=(0.0, 0.0, 0.0, 1.0))
DARK = Material("dark_graphite", rgba=(0.08, 0.085, 0.09, 1.0))
METAL = Material("brushed_metal", rgba=(0.55, 0.55, 0.52, 1.0))
LCD = Material("blue_black_lcd", rgba=(0.02, 0.08, 0.11, 1.0))
DIFFUSER = Material("milky_diffuser", rgba=(0.82, 0.90, 0.96, 0.58))
CARD = Material("white_bounce_card", rgba=(0.96, 0.96, 0.92, 1.0))
def _rounded_box_mesh(
    size: tuple[float, float, float],
    center: tuple[float, float, float],
    radius: float,
    name: str,
):
    shape = (
        cq.Workplane("XY")
        .box(size[0], size[1], size[2])
        .edges("|Z")
        .fillet(radius)
        .translate(center)
    )
    return mesh_from_cadquery(shape, name, tolerance=0.0006, angular_tolerance=0.08)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="professional_camera_flash")

    body = model.part("body")
    body.visual(
        Box((0.070, 0.052, 0.007)),
        origin=Origin(xyz=(0.000, 0.000, 0.0035)),
        material=METAL,
        name="foot_plate",
    )
    body.visual(
        Box((0.052, 0.040, 0.008)),
        origin=Origin(xyz=(0.000, 0.000, 0.011)),
        material=DARK,
        name="shoe_block",
    )
    body.visual(
        _rounded_box_mesh((0.060, 0.078, 0.120), (-0.005, 0.0, 0.075), 0.008, "body_shell"),
        material=BLACK,
        name="body_shell",
    )
    body.visual(
        Box((0.002, 0.062, 0.083)),
        origin=Origin(xyz=(-0.036, 0.000, 0.082)),
        material=DARK,
        name="rear_panel",
    )
    body.visual(
        Box((0.001, 0.052, 0.027)),
        origin=Origin(xyz=(-0.0375, 0.000, 0.108)),
        material=LCD,
        name="lcd_window",
    )
    body.visual(
        Cylinder(radius=0.031, length=0.008),
        origin=Origin(xyz=(0.000, 0.000, 0.139)),
        material=DARK,
        name="swivel_socket",
    )

    dial = model.part("rear_dial")
    dial.visual(
        Cylinder(radius=0.018, length=0.005),
        origin=Origin(xyz=(-0.0025, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=RUBBER,
        name="dial_wheel",
    )
    dial.visual(
        Cylinder(radius=0.006, length=0.006),
        origin=Origin(xyz=(-0.0055, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=DARK,
        name="dial_hub",
    )
    model.articulation(
        "body_to_rear_dial",
        ArticulationType.REVOLUTE,
        parent=body,
        child=dial,
        origin=Origin(xyz=(-0.037, 0.0, 0.041)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.4, velocity=4.0, lower=-math.pi, upper=math.pi),
    )

    button_locations = [
        (-0.019, 0.063),
        (0.019, 0.063),
        (-0.019, 0.080),
        (0.019, 0.080),
    ]
    for index, (y, z) in enumerate(button_locations):
        button = model.part(f"button_{index}")
        button.visual(
            Box((0.004, 0.014, 0.009)),
            origin=Origin(xyz=(-0.002, 0.0, 0.0)),
            material=RUBBER,
            name="button_cap",
        )
        model.articulation(
            f"body_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(xyz=(-0.037, y, z)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=1.0, velocity=0.03, lower=0.0, upper=0.002),
        )

    yoke = model.part("yoke")
    yoke.visual(
        Cylinder(radius=0.030, length=0.006),
        origin=Origin(xyz=(0.000, 0.000, 0.003)),
        material=BLACK,
        name="swivel_disk",
    )
    yoke.visual(
        Box((0.032, 0.050, 0.025)),
        origin=Origin(xyz=(0.014, 0.000, 0.018)),
        material=BLACK,
        name="neck_block",
    )
    yoke.visual(
        Box((0.022, 0.150, 0.050)),
        origin=Origin(xyz=(0.026, 0.000, 0.030)),
        material=BLACK,
        name="rear_bridge",
    )
    yoke.visual(
        Box((0.062, 0.018, 0.080)),
        origin=Origin(xyz=(0.061, -0.067, 0.038)),
        material=BLACK,
        name="yoke_arm_0",
    )
    yoke.visual(
        Cylinder(radius=0.014, length=0.018),
        origin=Origin(xyz=(0.055, -0.067, 0.042), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=DARK,
        name="tilt_bushing_0",
    )
    yoke.visual(
        Box((0.062, 0.018, 0.080)),
        origin=Origin(xyz=(0.061, 0.067, 0.038)),
        material=BLACK,
        name="yoke_arm_1",
    )
    yoke.visual(
        Cylinder(radius=0.014, length=0.018),
        origin=Origin(xyz=(0.055, 0.067, 0.042), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=DARK,
        name="tilt_bushing_1",
    )
    model.articulation(
        "body_to_yoke",
        ArticulationType.REVOLUTE,
        parent=body,
        child=yoke,
        origin=Origin(xyz=(0.000, 0.000, 0.143)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=4.0, velocity=2.0, lower=-math.pi, upper=math.pi),
    )

    head = model.part("head")
    head.visual(
        Box((0.011, 0.104, 0.080)),
        origin=Origin(xyz=(0.0005, 0.000, -0.005)),
        material=BLACK,
        name="rear_shell",
    )
    head.visual(
        Box((0.081, 0.104, 0.080)),
        origin=Origin(xyz=(0.0545, 0.000, -0.005)),
        material=BLACK,
        name="front_shell",
    )
    head.visual(
        Box((0.008, 0.009, 0.080)),
        origin=Origin(xyz=(0.010, -0.0475, -0.005)),
        material=BLACK,
        name="slot_rail_0",
    )
    head.visual(
        Box((0.008, 0.009, 0.080)),
        origin=Origin(xyz=(0.010, 0.0475, -0.005)),
        material=BLACK,
        name="slot_rail_1",
    )
    head.visual(
        Box((0.004, 0.086, 0.054)),
        origin=Origin(xyz=(0.097, 0.000, -0.004)),
        material=DIFFUSER,
        name="front_diffuser",
    )
    head.visual(
        Cylinder(radius=0.010, length=0.006),
        origin=Origin(xyz=(0.000, -0.055, 0.000), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=DARK,
        name="tilt_pin_0",
    )
    head.visual(
        Cylinder(radius=0.010, length=0.006),
        origin=Origin(xyz=(0.000, 0.055, 0.000), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=DARK,
        name="tilt_pin_1",
    )
    model.articulation(
        "yoke_to_head",
        ArticulationType.REVOLUTE,
        parent=yoke,
        child=head,
        origin=Origin(xyz=(0.055, 0.000, 0.042)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=4.0, velocity=2.0, lower=-0.17, upper=1.35),
    )

    card = model.part("bounce_card")
    card.visual(
        Box((0.008, 0.076, 0.072)),
        origin=Origin(xyz=(0.000, 0.000, -0.036)),
        material=CARD,
        name="card_insert",
    )
    model.articulation(
        "head_to_bounce_card",
        ArticulationType.PRISMATIC,
        parent=head,
        child=card,
        origin=Origin(xyz=(0.010, 0.000, 0.037)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.0, velocity=0.12, lower=0.0, upper=0.045),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
