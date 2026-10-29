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
import cadquery as cq
BODY_DEPTH = 0.046
BODY_WIDTH = 0.078
BODY_HEIGHT = 0.118
BODY_BOTTOM_Z = 0.024
BODY_TOP_Z = BODY_BOTTOM_Z + BODY_HEIGHT
BODY_REAR_X = -BODY_DEPTH / 2.0
HEAD_PIVOT_Z = 0.028
def _body_shell() -> object:
    return (
        cq.Workplane("XY")
        .box(BODY_DEPTH, BODY_WIDTH, BODY_HEIGHT)
        .edges("|Z")
        .fillet(0.004)
        .faces(">Z")
        .edges()
        .chamfer(0.003)
        .translate((0.0, 0.0, BODY_BOTTOM_Z + BODY_HEIGHT / 2.0))
    )
def _head_shell() -> object:
    return (
        cq.Workplane("XY")
        .box(0.070, 0.072, 0.050)
        .translate((0.025, 0.0, 0.009))
        .faces(">X")
        .edges()
        .chamfer(0.006)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="camera_flash")

    body_black = model.material("body_black", rgba=(0.16, 0.17, 0.18, 1.0))
    trim_black = model.material("trim_black", rgba=(0.10, 0.11, 0.12, 1.0))
    dark_grey = model.material("dark_grey", rgba=(0.26, 0.27, 0.29, 1.0))
    diffuser_white = model.material("diffuser_white", rgba=(0.95, 0.95, 0.93, 0.92))
    glass_blue = model.material("glass_blue", rgba=(0.17, 0.29, 0.35, 0.58))
    button_black = model.material("button_black", rgba=(0.12, 0.12, 0.13, 1.0))
    foot_dark = model.material("foot_dark", rgba=(0.14, 0.15, 0.16, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shell(), "flash_body_shell"),
        material=body_black,
        name="shell",
    )
    body.visual(
        Box((0.046, 0.030, 0.006)),
        origin=Origin(xyz=(0.0, 0.0, 0.003)),
        material=foot_dark,
        name="foot_plate",
    )
    body.visual(
        Box((0.020, 0.018, 0.004)),
        origin=Origin(xyz=(0.0, 0.0, -0.002)),
        material=trim_black,
        name="shoe_rail",
    )
    body.visual(
        Box((0.028, 0.018, 0.018)),
        origin=Origin(xyz=(0.0, 0.0, 0.015)),
        material=foot_dark,
        name="foot_stem",
    )
    body.visual(
        Cylinder(radius=0.019, length=0.003),
        origin=Origin(xyz=(0.0, 0.0, BODY_TOP_Z + 0.0015)),
        material=trim_black,
        name="swivel_collar",
    )
    body.visual(
        Box((0.003, 0.056, 0.038)),
        origin=Origin(xyz=(BODY_REAR_X - 0.0015, 0.0, 0.103)),
        material=dark_grey,
        name="lcd_bezel",
    )
    body.visual(
        Box((0.0015, 0.044, 0.026)),
        origin=Origin(xyz=(BODY_REAR_X - 0.0030, 0.0, 0.103)),
        material=glass_blue,
        name="lcd_glass",
    )
    body.visual(
        Box((0.0025, 0.066, 0.076)),
        origin=Origin(xyz=(BODY_REAR_X - 0.00125, 0.0, 0.076)),
        material=dark_grey,
        name="control_plate",
    )

    yoke = model.part("yoke")
    yoke.visual(
        Cylinder(radius=0.018, length=0.004),
        origin=Origin(xyz=(0.0, 0.0, 0.005)),
        material=trim_black,
        name="turntable",
    )
    yoke.visual(
        Box((0.007, 0.083, 0.016)),
        origin=Origin(xyz=(-0.0185, 0.0, 0.013)),
        material=body_black,
        name="rear_bridge",
    )
    yoke.visual(
        Box((0.018, 0.006, 0.034)),
        origin=Origin(xyz=(-0.006, -0.0420, 0.023)),
        material=body_black,
        name="arm_0",
    )
    yoke.visual(
        Box((0.018, 0.006, 0.034)),
        origin=Origin(xyz=(-0.006, 0.0420, 0.023)),
        material=body_black,
        name="arm_1",
    )
    yoke.visual(
        Cylinder(radius=0.0045, length=0.008),
        origin=Origin(xyz=(-0.001, -0.0420, HEAD_PIVOT_Z), rpy=(1.57079632679, 0.0, 0.0)),
        material=trim_black,
        name="pivot_cap_0",
    )
    yoke.visual(
        Cylinder(radius=0.0045, length=0.008),
        origin=Origin(xyz=(-0.001, 0.0420, HEAD_PIVOT_Z), rpy=(1.57079632679, 0.0, 0.0)),
        material=trim_black,
        name="pivot_cap_1",
    )

    head = model.part("head")
    head.visual(
        mesh_from_cadquery(_head_shell(), "flash_head_shell"),
        material=body_black,
        name="shell",
    )
    head.visual(
        Box((0.004, 0.062, 0.034)),
        origin=Origin(xyz=(0.056, 0.0, 0.009)),
        material=diffuser_white,
        name="diffuser",
    )
    head.visual(
        Box((0.006, 0.070, 0.042)),
        origin=Origin(xyz=(0.053, 0.0, 0.009)),
        material=trim_black,
        name="diffuser_frame",
    )
    head.visual(
        Cylinder(radius=0.0045, length=0.003),
        origin=Origin(xyz=(-0.001, -0.0375, 0.0), rpy=(1.57079632679, 0.0, 0.0)),
        material=trim_black,
        name="trunnion_0",
    )
    head.visual(
        Cylinder(radius=0.0045, length=0.003),
        origin=Origin(xyz=(-0.001, 0.0375, 0.0), rpy=(1.57079632679, 0.0, 0.0)),
        material=trim_black,
        name="trunnion_1",
    )

    model.articulation(
        "body_to_yoke",
        ArticulationType.REVOLUTE,
        parent=body,
        child=yoke,
        origin=Origin(xyz=(0.0, 0.0, BODY_TOP_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=6.0,
            velocity=2.5,
            lower=-1.9,
            upper=1.9,
        ),
    )
    model.articulation(
        "yoke_to_head",
        ArticulationType.REVOLUTE,
        parent=yoke,
        child=head,
        origin=Origin(xyz=(-0.001, 0.0, HEAD_PIVOT_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=4.0,
            velocity=2.0,
            lower=0.0,
            upper=1.35,
        ),
    )

    dial = model.part("dial")
    dial.visual(
        Cylinder(radius=0.018, length=0.0035),
        origin=Origin(xyz=(-0.00175, 0.0, 0.0), rpy=(0.0, 1.57079632679, 0.0)),
        material=button_black,
        name="outer_ring",
    )
    dial.visual(
        Cylinder(radius=0.0145, length=0.005),
        origin=Origin(xyz=(-0.0025, 0.0, 0.0), rpy=(0.0, 1.57079632679, 0.0)),
        material=dark_grey,
        name="dial_face",
    )
    dial.visual(
        Cylinder(radius=0.0085, length=0.0055),
        origin=Origin(xyz=(-0.00275, 0.0, 0.0), rpy=(0.0, 1.57079632679, 0.0)),
        material=trim_black,
        name="hub",
    )
    dial.visual(
        Box((0.0015, 0.004, 0.010)),
        origin=Origin(xyz=(-0.0042, 0.0, 0.012)),
        material=diffuser_white,
        name="indicator",
    )
    model.articulation(
        "body_to_dial",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=dial,
        origin=Origin(xyz=(BODY_REAR_X - 0.0025, 0.0, 0.067)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.15, velocity=5.5),
    )

    key_specs = (
        ("top_key", (0.0, 0.093), (0.014, 0.018, 0.0040), (0.010, 0.014, 0.0015)),
        ("bottom_key", (0.0, 0.041), (0.014, 0.018, 0.0040), (0.010, 0.014, 0.0015)),
        ("left_key", (-0.028, 0.067), (0.014, 0.014, 0.011), (0.010, 0.010, 0.0015)),
        ("right_key", (0.028, 0.067), (0.014, 0.014, 0.011), (0.010, 0.010, 0.0015)),
    )
    for key_name, (key_y, key_z), cap_size, pad_size in key_specs:
        key = model.part(key_name)
        key.visual(
            Box(cap_size),
            origin=Origin(xyz=(-cap_size[0] / 2.0, 0.0, 0.0)),
            material=button_black,
            name="keycap",
        )
        key.visual(
            Box(pad_size),
            origin=Origin(xyz=(-cap_size[0] - pad_size[0] / 2.0 + 0.0015, 0.0, 0.0)),
            material=dark_grey,
            name="pad",
        )
        model.articulation(
            f"body_to_{key_name}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=key,
            origin=Origin(xyz=(BODY_REAR_X - 0.0025, key_y, key_z)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(
                effort=8.0,
                velocity=0.06,
                lower=0.0,
                upper=0.0018,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
